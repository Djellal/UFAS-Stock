"""
Management command to recalculate stock_quantity for all products.
For assets: counts available InventoryItems.
For consumables: sums all StockMovement quantities.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from inventory.models import Product


class Command(BaseCommand):
    help = 'Recalculate stock_quantity for all products based on their nature'

    def add_arguments(self, parser):
        parser.add_argument(
            '--asset-only',
            action='store_true',
            help='Only recalculate for asset products',
        )
        parser.add_argument(
            '--consumable-only',
            action='store_true',
            help='Only recalculate for consumable products',
        )

    def handle(self, *args, **options):
        if options['asset_only']:
            products = Product.objects.filter(nature='asset')
            product_type = 'asset'
        elif options['consumable_only']:
            products = Product.objects.filter(nature='consumable')
            product_type = 'consumable'
        else:
            products = Product.objects.all()
            product_type = 'all'

        total = products.count()
        updated = 0

        self.stdout.write(f'Processing {total} {product_type} products...')

        for product in products:
            old_quantity = product.stock_quantity

            if product.is_asset:
                # For assets: count available items
                new_quantity = product.items.filter(status='available').count()
            else:
                # For consumables: sum all movement quantities
                new_quantity = product.stock_movements.aggregate(
                    total=Sum('quantity')
                )['total'] or 0

            if old_quantity != new_quantity:
                product.stock_quantity = new_quantity
                product.save(update_fields=['stock_quantity', 'updated_at'])
                updated += 1
                self.stdout.write(
                    f'  {product.name}: {old_quantity} -> {new_quantity}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Finished: {updated} of {total} products updated.'
            )
        )
