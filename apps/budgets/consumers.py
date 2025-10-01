import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Expense, TypingStatus, Comment, Collaborator


class ExpenseCommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        self.user = self.scope.get("user", AnonymousUser())
        self.expense_id = self.scope['url_route']['kwargs']['expense_id']
        self.room_group_name = f'expense_{self.expense_id}_comments'
        
        print(f"Connection attempt - User: {self.user}, Expense ID: {self.expense_id}")
        
        # Check authentication first
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            print("Authentication failed: Anonymous or unauthenticated user")
            await self.send_error_and_close("authentication_failed", "Authentication required. Please provide a valid token.")
            return
        
        # Check if user is collaborator
        is_collaborator_result = await self.is_collaborator()
        if not is_collaborator_result:
            print(f"Authorization failed: User {self.user.email} is not a collaborator for expense {self.expense_id}")
            await self.send_error_and_close("authorization_failed", "You are not authorized to access this expense.")
            return
        
        # All checks passed - accept connection
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send success authentication message
        await self.send(text_data=json.dumps({
            'type': 'auth_status',
            'authenticated': True,
            'user': {
                'id': str(self.user.id),
                'email': self.user.email,
                'username': getattr(self.user, 'firstname', self.user.firstname)
            },
            'message': f'Successfully connected as {self.user.email}'
        }))
        print(f"Connection successful for user: {self.user.email}")

    async def send_error_and_close(self, error_type, message):
        """Send error message and close connection"""
        try:
            # Accept connection briefly to send error message
            await self.accept()
            
            # Send error message
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error_type': error_type,
                'message': message,
                'authenticated': False
            }))
            
            # Close connection with appropriate code
            if error_type == "authentication_failed":
                await self.close(code=4001)  # Custom code for authentication failure
            elif error_type == "authorization_failed":
                await self.close(code=4003)  # Custom code for authorization failure
            else:
                await self.close(code=4000)  # Generic client error
                
        except Exception as e:
            print(f"Error sending error message: {e}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        print(f"User {getattr(self.user, 'email', 'Unknown')} disconnected with code: {close_code}")
        
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        # Clear typing status only if user was authenticated
        if not isinstance(self.user, AnonymousUser) and self.user.is_authenticated:
            await self.clear_typing_status()

    async def receive(self, text_data):
        # Double-check authentication on each message (for token expiration)
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error_type': 'token_expired',
                'message': 'Your session has expired. Please reconnect.',
                'authenticated': False
            }))
            await self.close(code=4002)  # Custom code for token expiration
            return
            
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'typing':
                is_typing = text_data_json.get('is_typing', False)
                await self.update_typing_status(is_typing)
                
                # Broadcast typing status
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_status',
                        'user': await self.get_user_name(),
                        'is_typing': is_typing
                    }
                )
            
            elif message_type == 'comment':
                comment_data = text_data_json.get('comment', {})
                print(f"Comment data received: {comment_data}")
                
                # Validate required fields
                if not comment_data.get('content'):
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error_type': 'validation_failed',
                        'message': 'Comment content is required'
                    }))
                    return
                
                # Create comment with validation
                result = await self.create_comment(comment_data)
                
                if result.get('success'):
                    # Broadcast successful comment creation
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'new_comment',
                            'comment': result['comment']
                        }
                    )
                    
                    # Send success confirmation to sender
                    await self.send(text_data=json.dumps({
                        'type': 'comment_created',
                        'comment': result['comment'],
                        'message': 'Comment created successfully'
                    }))
                else:
                    # Send error response
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error_type': result.get('error', 'unknown_error'),
                        'message': result.get('message', 'Failed to create comment')
                    }))
                    
            elif message_type == 'get_comments':
                # Optional: Load existing comments
                comments = await self.get_comments()
                await self.send(text_data=json.dumps({
                    'type': 'comments_list',
                    'comments': comments
                }))
    
                    
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error_type': 'invalid_json',
                'message': 'Invalid JSON format in message.'
            }))
        except Exception as e:
            print(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error_type': 'server_error',
                'message': 'An unexpected error occurred.'
            }))

    async def typing_status(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user': event['user'],
            'is_typing': event['is_typing']
        }))

    async def new_comment(self, event):
        # Send comment to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': event['comment']
        }))

    @database_sync_to_async
    def is_collaborator(self):
        try:
            expense = Expense.objects.get(id=self.expense_id)
            print("Is Collab Expense: ", expense)
            return expense.budget.event.collaborators.filter(
                collaborator__user=self.user
            ).exists()
        except Expense.DoesNotExist:
            print(f"Expense {self.expense_id} not found")
            return False
        except Exception as e:
            print(f"Error checking collaborator status: {e}")
            return False

    @database_sync_to_async
    def get_user_name(self):
        return f"{self.user.firstname} {self.user.lastname}".strip() or self.user.email

    @database_sync_to_async
    def update_typing_status(self, is_typing):
        print("Check Is Typing: ", is_typing)
        try:
            expense = Expense.objects.get(id=self.expense_id)
            print("Update Typing Expense: ", expense)
            
            collaborator = Collaborator.objects.get(
                event=expense.budget.event,
                user=self.user
            )
            print("Expense After: ", expense)
            print("Collaborator: ", collaborator)
            
            typing_status, created = TypingStatus.objects.get_or_create(
                expense=expense,
                collaborator=collaborator,
                defaults={'is_typing': is_typing}
            )
            print("Typing Status: ", typing_status)
            print("Created: ", created)
            
            if not created:
                typing_status.is_typing = is_typing
                typing_status.save()
                
        except Expense.DoesNotExist:
            print(f"Expense {self.expense_id} not found in update_typing_status")
        except Collaborator.DoesNotExist:
            print(f"Collaborator not found for user {self.user.email} and expense {self.expense_id}")
        except Exception as e:
            print(f"Error in update_typing_status: {e}")

    @database_sync_to_async
    def clear_typing_status(self):
        try:
            expense = Expense.objects.get(id=self.expense_id)
            collaborator = Collaborator.objects.get(
                event=expense.budget.event,
                user=self.user
            )

            TypingStatus.objects.filter(
                expense=expense,
                collaborator=collaborator
            ).delete()
            print(f"Cleared typing status for user {self.user.email}")
            
        except (Expense.DoesNotExist, Collaborator.DoesNotExist) as e:
            print(f"Error clearing typing status: {e}")
        except Exception as e:
            print(f"Unexpected error clearing typing status: {e}")

    # @database_sync_to_async
    # def create_comment(self, comment_data):
    #     try:
    #         from django.contrib.contenttypes.models import ContentType
            
    #         expense = Expense.objects.get(id=self.expense_id)
    #         collaborator = Collaborator.objects.get(
    #             event=expense.budget.event,
    #             user=self.user
    #         )
    #         expense_content_type = ContentType.objects.get_for_model(Expense)
            
    #         comment = Comment.objects.create(
    #             content_type=expense_content_type,
    #             object_id=str(expense.id),
    #             author=collaborator,
    #             content=comment_data.get('content', '')
    #         )
            
    #         return {
    #             'id': str(comment.id),
    #             'content': comment.content,
    #             'author': f"{collaborator.user.firstname} {collaborator.user.lastname}".strip() or collaborator.user.email,
    #             'created_at': comment.created_at.isoformat()
    #         }
    #     except Exception as e:
    #         print(f"Error creating comment: {e}")
    #         return None
        
    
    @database_sync_to_async
    def create_comment(self, comment_data):
        """Create comment with same validation as HTTP API"""
        try:
            from django.contrib.contenttypes.models import ContentType
            
            # Get and validate expense
            expense = Expense.objects.get(id=self.expense_id)
            
            # Get collaborator (same as HTTP API)
            try:
                collaborator = Collaborator.objects.get(
                    event=expense.budget.event,
                    user=self.user
                )
            except Collaborator.DoesNotExist:
                print(f"User {self.user.email} is not a collaborator for expense {self.expense_id}")
                return {
                    'error': 'authorization_failed',
                    'message': 'Only event collaborators can comment on expenses'
                }
            
            # Validate content (same as serializer)
            content = comment_data.get('content', '').strip()
            if not content:
                return {
                    'error': 'validation_failed',
                    'message': 'Comment content cannot be empty'
                }
            
            # Handle parent comment validation
            parent_comment = None
            parent_id = comment_data.get('parent')
            
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    
                    # Validate parent belongs to same expense
                    expense_content_type = ContentType.objects.get_for_model(Expense)
                    if (parent_comment.content_type != expense_content_type or 
                        str(parent_comment.object_id) != str(expense.id)):
                        return {
                            'error': 'validation_failed',
                            'message': 'Parent comment must belong to the same expense'
                        }
                    
                    # Prevent deep nesting (same as HTTP API)
                    if parent_comment.parent is not None:
                        return {
                            'error': 'validation_failed',
                            'message': 'Cannot reply to a reply. Please reply to the original comment.'
                        }
                        
                except Comment.DoesNotExist:
                    return {
                        'error': 'validation_failed',
                        'message': 'Parent comment not found'
                    }
            
            # Create the comment
            expense_content_type = ContentType.objects.get_for_model(Expense)
            comment = Comment.objects.create(
                content_type=expense_content_type,
                object_id=str(expense.id),
                author=collaborator,
                content=content,
                parent=parent_comment
            )
            
            # Return success response with all comment details
            return {
                'success': True,
                'comment': {
                    'id': str(comment.id),
                    'content': comment.content,
                    'author': {
                        'id': str(collaborator.user.id),
                        'name': f"{collaborator.user.first_name} {collaborator.user.last_name}".strip() or collaborator.user.email,
                        'email': collaborator.user.email
                    },
                    'parent_id': str(parent_comment.id) if parent_comment else None,
                    'is_reply': parent_comment is not None,
                    'created_at': comment.created_at.isoformat(),
                    'replies': []  # New comments don't have replies yet
                }
            }
            
        except Expense.DoesNotExist:
            print(f"Expense {self.expense_id} not found")
            return {
                'error': 'not_found',
                'message': 'Expense not found'
            }
        except Exception as e:
            print(f"Error creating comment: {e}")
            return {
                'error': 'server_error',
                'message': 'An unexpected error occurred while creating the comment'
            }
        
    @database_sync_to_async
    def get_comments(self):
        """Get all comments for the expense (optional method for loading existing comments)"""
        try:
            from django.contrib.contenttypes.models import ContentType
            
            expense_content_type = ContentType.objects.get_for_model(Expense)
            comments = Comment.objects.filter(
                content_type=expense_content_type,
                object_id=str(self.expense_id),
                parent=None  # Only root comments
            ).select_related('author__user').prefetch_related('replies__author__user').order_by('created_at')
            
            result = []
            for comment in comments:
                comment_data = {
                    'id': str(comment.id),
                    'content': comment.content,
                    'author': {
                        'id': str(comment.author.user.id),
                        'name': f"{comment.author.user.first_name} {comment.author.user.last_name}".strip() or comment.author.user.email,
                        'email': comment.author.user.email
                    },
                    'created_at': comment.created_at.isoformat(),
                    'is_reply': False,
                    'replies': []
                }
                
                # Add replies
                for reply in comment.replies.all().order_by('created_at'):
                    reply_data = {
                        'id': str(reply.id),
                        'content': reply.content,
                        'author': {
                            'id': str(reply.author.user.id),
                            'name': f"{reply.author.user.first_name} {reply.author.user.last_name}".strip() or reply.author.user.email,
                            'email': reply.author.user.email
                        },
                        'parent_id': str(comment.id),
                        'created_at': reply.created_at.isoformat(),
                        'is_reply': True
                    }
                    comment_data['replies'].append(reply_data)
                
                result.append(comment_data)
            
            return result
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []