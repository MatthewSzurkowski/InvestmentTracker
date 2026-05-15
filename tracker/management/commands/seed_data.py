from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import Account, Asset, AssetValueHistory, Contribution
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

        assets_data = [
            {
                'account': accounts['TFSA'],
                'name': 'Vanguard FTSE Canada All Cap Index ETF',
                'ticker': 'VCN',
                'asset_type': 'ETF',
                'purchase_date': date(current_year, 1, 15),
                'purchase_price': Decimal('45.20'),
                'quantity': Decimal('50.000000'),
                'history': [
                    (date(current_year, 2, 1), Decimal('46.10')),
                    (date(current_year, 3, 1), Decimal('47.50')),
                    (date(current_year, 4, 1), Decimal('46.80')),
                ],
            },
            {
                'account': accounts['TFSA'],
                'name': 'iShares Core S&P 500 ETF',
                'ticker': 'XUS',
                'asset_type': 'ETF',
                'purchase_date': date(current_year, 2, 10),
                'purchase_price': Decimal('62.30'),
                'quantity': Decimal('30.000000'),
                'history': [
                    (date(current_year, 3, 1), Decimal('64.50')),
                    (date(current_year, 4, 1), Decimal('63.20')),
                ],
            },
            {
                'account': accounts['RRSP'],
                'name': 'Royal Bank of Canada',
                'ticker': 'RY',
                'asset_type': 'Stock',
                'purchase_date': date(current_year, 1, 20),
                'purchase_price': Decimal('128.50'),
                'quantity': Decimal('20.000000'),
                'history': [
                    (date(current_year, 2, 15), Decimal('131.20')),
                    (date(current_year, 3, 15), Decimal('133.80')),
                ],
            },
            {
                'account': accounts['RRSP'],
                'name': 'BMO Aggregate Bond Index ETF',
                'ticker': 'ZAG',
                'asset_type': 'ETF',
                'purchase_date': date(current_year, 1, 20),
                'purchase_price': Decimal('14.25'),
                'quantity': Decimal('200.000000'),
                'history': [
                    (date(current_year, 2, 15), Decimal('14.40')),
                    (date(current_year, 3, 15), Decimal('14.35')),
                ],
            },
            {
                'account': accounts['FHSA'],
                'name': 'Vanguard Balanced ETF Portfolio',
                'ticker': 'VBAL',
                'asset_type': 'ETF',
                'purchase_date': date(current_year, 3, 5),
                'purchase_price': Decimal('33.80'),
                'quantity': Decimal('100.000000'),
                'history': [
                    (date(current_year, 4, 1), Decimal('34.50')),
                ],
            },
            {
                'account': accounts['Non-Registered'],
                'name': 'Bitcoin',
                'ticker': 'BTC',
                'asset_type': 'Crypto',
                'purchase_date': date(current_year, 1, 5),
                'purchase_price': Decimal('52000.00'),
                'quantity': Decimal('0.100000'),
                'history': [
                    (date(current_year, 2, 1), Decimal('58000.00')),
                    (date(current_year, 3, 1), Decimal('65000.00')),
                    (date(current_year, 4, 1), Decimal('60000.00')),
                ],
            },
        ]

        for ad in assets_data:
            history = ad.pop('history')
            asset, created = Asset.objects.get_or_create(
                user=user,
                account=ad['account'],
                ticker=ad['ticker'],
                defaults=ad,
            )
            if created:
                self.stdout.write(f'  Asset: {asset.name}')
            for h_date, h_value in history:
                AssetValueHistory.objects.get_or_create(asset=asset, date=h_date, defaults={'value': h_value})

        self.stdout.write(self.style.SUCCESS('Seed data created. Login: demo / demo1234'))
