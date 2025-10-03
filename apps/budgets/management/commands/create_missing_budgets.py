# apps/budget/management/commands/create_missing_budgets.py
from django.core.management.base import BaseCommand
from djmoney.money import Money
from apps.events.models import Event
from apps.budgets.models import Budget

class Command(BaseCommand):
    help = 'Create budgets for existing events that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating budgets',
        )

    def handle(self, *args, **options):
        # Find events without budgets
        events_without_budgets = Event.objects.filter(budget__isnull=True)
        total_events = events_without_budgets.count()
        
        if total_events == 0:
            self.stdout.write(
                self.style.SUCCESS('All events already have budgets!')
            )
            return
        
        self.stdout.write(f'Found {total_events} events without budgets')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No budgets will be created')
            )
            for event in events_without_budgets:
                self.stdout.write(f'Would create budget for: {event.name} (ID: {event.id})')
            return
        
        created_count = 0
        failed_count = 0
        
        for event in events_without_budgets:
            try:
                budget, created = Budget.objects.get_or_create(
                    event=event,
                    defaults={
                        'estimated_amount': Money(0, 'NGN'),
                        'is_enabled': False
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created budget for: {event.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Budget already exists for: {event.name}')
                    )
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to create budget for {event.name}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('-' * 50)
        self.stdout.write(f'Total events processed: {total_events}')
        self.stdout.write(f'Budgets created: {created_count}')
        if failed_count > 0:
            self.stdout.write(f'Failed: {failed_count}')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} budgets!'
                )
            )