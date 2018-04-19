# -*- coding: UTF-8 -*-
from budget_app.loaders import PaymentsLoader
from budget_app.models import Budget

import dateutil.parser
import re


class CastellonPaymentsLoader(PaymentsLoader):

    # make year data available in the class and call super
    def load(self, entity, year, path):
        self.year = year
        PaymentsLoader.load(self, entity, year, path)

    # Parse an input line into fields
    def parse_item(self, budget, line):
        # We got the functional codes
        fc_code = line[7]

        # But we got some lines with wrong classification data
        if not re.search(r'^\d{5}$', fc_code):
            return None

        # First two digits of the programme make the policy id
        policy_id = fc_code[:2]

        # But what we want as area is the policy description
        policy = Budget.objects.get_all_descriptions(budget.entity)['functional'][policy_id]

        # We got the institutional code
        ic_code = line[9].zfill(3)

        # For years from 2016 we check whether we need to amend the institutional code
        if self.year not in ['2013', '2014', '2015']:
            ic_code = '1'+ic_code[1:]

        # We only get the year number, so we assign all the entries to the
        # year's last day
        date = line[1]
        date = dateutil.parser.parse(date).strftime("%Y-%m-%d")

        # Normalize payee data
        payee = line[3]
        payee = ('Anonimizado' if payee == '*** Anonimizado ***' else payee)

        # We got some anonymized entries
        anonymized = False
        anonymized = (True if payee == "Anonimizado" else anonymized)

        # We got the description
        description = line[5]

        # We got a localized amount (e.g. 42.732,08) sometimes including the currency symbol (e.g. 70.162,49 €)
        amount = re.sub(r'[^\d.,-]+', '', line[6])
        amount = self._read_spanish_number(amount)

        return {
            'area': policy,
            'programme': None,
            'fc_code': None,  # We don't try (yet) to have foreign keys to existing records
            'ec_code': None,
            'ic_code': ic_code,
            'date': date,
            'payee': payee,
            'anonymized': anonymized,
            'description': description,
            'amount': amount
        }