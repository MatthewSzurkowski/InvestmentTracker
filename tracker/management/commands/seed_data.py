from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import Account, Asset, Trade, AssetPriceHistory
from datetime import date
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        user, created = User.objects.get_or_create(username='demo', defaults={'email': 'demo@example.com'})
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write('  Created user: demo / demo1234')

        current_year = date.today().year

        # Create accounts
        accounts_data = [
            ('TFSA', current_year, Decimal('7000.00')),
            ('RRSP', current_year, Decimal('31560.00')),
            ('FHSA', current_year, Decimal('8000.00')),
            ('Non-Registered', current_year, Decimal('0.00')),
        ]

        accounts = {}
        for acc_type, year, limit in accounts_data:
            acc, _ = Account.objects.get_or_create(
                user=user, type=acc_type, year=year,
                defaults={'annual_contribution_limit': limit}
            )
            accounts[acc_type] = acc
            self.stdout.write(f'  Account: {acc_type} {year}')

        # Create securities (Assets)
        securities_data = [
            {'ticker': 'VCN', 'name': 'Vanguard FTSE Canada All Cap Index ETF', 'type': 'ETF', 'currency': 'CAD'},
            {'ticker': 'XUS', 'name': 'iShares Core S&P 500 ETF', 'type': 'ETF', 'currency': 'CAD'},
            {'ticker': 'RY', 'name': 'Royal Bank of Canada', 'type': 'Stock', 'currency': 'CAD'},
            {'ticker': 'ZAG', 'name': 'BMO Aggregate Bond Index ETF', 'type': 'ETF', 'currency': 'CAD'},
            {'ticker': 'XEQT', 'name': 'Vanguard Balanced ETF Portfolio', 'type': 'ETF', 'currency': 'CAD'},
            {'ticker': 'BTC', 'name': 'Bitcoin', 'type': 'Crypto', 'currency': 'USD'},
        ]

        assets = {}
        for sec in securities_data:
            asset, created = Asset.objects.get_or_create(
                user=user,
                ticker=sec['ticker'],
                defaults={
                    'name': sec['name'],
                    'asset_type': sec['type'],
                    'currency': sec['currency'],
                }
            )
            assets[sec['ticker']] = asset
            if created:
                self.stdout.write(f'  Security: {asset.ticker} - {asset.name}')

        # Create trades with price history
        trades_data = [
            {
                'asset': 'VCN',
                'account': 'TFSA',
                'type': 'buy',
                'qty': Decimal('50'),
                'price': Decimal('45.20'),
                'date': date(current_year, 1, 15),
                'prices': [(date(current_year, 2, 1), Decimal('46.10')), (date(current_year, 3, 1), Decimal('47.50')), (date(current_year, 4, 1), Decimal('46.80'))],
            },
            {
                'asset': 'XUS',
                'account': 'TFSA',
                'type': 'buy',
                'qty': Decimal('30'),
                'price': Decimal('62.30'),
                'date': date(current_year, 2, 10),
                'prices': [(date(current_year, 3, 1), Decimal('64.50')), (date(current_year, 4, 1), Decimal('63.20'))],
            },
            {
                'asset': 'RY',
                'account': 'RRSP',
                'type': 'buy',
                'qty': Decimal('20'),
                'price': Decimal('128.50'),
                'date': date(current_year, 1, 20),
                'prices': [(date(current_year, 2, 15), Decimal('131.20')), (date(current_year, 3, 15), Decimal('133.80'))],
            },
            {
                'asset': 'ZAG',
                'account': 'RRSP',
                'type': 'buy',
                'qty': Decimal('200'),
                'price': Decimal('14.25'),
                'date': date(current_year, 1, 20),
                'prices': [(date(current_year, 2, 15), Decimal('14.40')), (date(current_year, 3, 15), Decimal('14.35'))],
            },
            {
                'asset': 'XEQT',
                'account': 'FHSA',
                'type': 'buy',
                'qty': Decimal('100'),
                'price': Decimal('33.80'),
                'date': date(current_year, 3, 5),
                'prices': [(date(current_year, 4, 1), Decimal('34.50'))],
            },
            {
                'asset': 'BTC',
                'account': 'Non-Registered',
                'type': 'buy',
                'qty': Decimal('0.1'),
                'price': Decimal('52000.00'),
                'date': date(current_year, 1, 5),
                'prices': [(date(current_year, 2, 1), Decimal('58000.00')), (date(current_year, 3, 1), Decimal('65000.00')), (date(current_year, 4, 1), Decimal('60000.00'))],
            },
        ]

        for td in trades_data:
            asset = assets[td['asset']]
            account = accounts[td['account']]
            trade_year = td['date'].year

            trade, _ = Trade.objects.get_or_create(
                user=user,
                asset=asset,
                account=account,
                date=td['date'],
                defaults={
                    'trade_type': td['type'],
                    'quantity': td['qty'],
                    'price': td['price'],
                    'year': trade_year,
                }
            )
            self.stdout.write(f'    Trade: {td["type"].upper()} {td["qty"]} {td["asset"]} @ ${td["price"]}')

            # Create price history
            for price_date, price_value in td['prices']:
                AssetPriceHistory.objects.get_or_create(
                    asset=asset,
                    date=price_date,
                    defaults={'price': price_value}
                )

        # Set initial prices for all assets
        initial_prices = {
            'VCN': Decimal('46.80'),
            'XUS': Decimal('63.20'),
            'RY': Decimal('133.80'),
            'ZAG': Decimal('14.35'),
            'XEQT': Decimal('34.50'),
            'BTC': Decimal('60000.00'),
        }

        for ticker, price in initial_prices.items():
            asset = assets[ticker]
            latest_price = asset.price_history.order_by('-date').first()
            if not latest_price or latest_price.price != price:
                AssetPriceHistory.objects.get_or_create(
                    asset=asset,
                    date=date.today(),
                    defaults={'price': price}
                )

        self.stdout.write(self.style.SUCCESS('Seed data created. Login: demo / demo1234'))
