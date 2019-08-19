# -*- coding: UTF-8 -*-
from budget_app.loaders import PaymentsLoader
from budget_app.models import Budget

import dateutil.parser
import re


class CastellonPaymentsLoader(PaymentsLoader):

    # Parse an input line into fields
    def parse_item(self, budget, line):
        # We got the functional codes
        fc_code = line[6].zfill(5)

        # But we got some lines with wrong classification data
        if fc_code == '00000' or not re.search(r'^\d{5}$', fc_code):
            return None

        # First two digits of the programme make the policy id
        policy_id = fc_code[:2]

        # But what we want as area is the policy description
        policy = Budget.objects.get_all_descriptions(budget.entity)['functional'][policy_id]

        # We got the institutional code
        ic_code = line[5].zfill(3)

        # For years from 2016 we check whether we need to amend the institutional code
        if budget.year not in [2013, 2014, 2015]:
            ic_code = '1'+ic_code[1:]

        # We only get the year number, so we assign all the entries to the
        # year's last day
        date = line[3]
        date = dateutil.parser.parse(date).strftime("%Y-%m-%d")

        # Normalize payee data
        payee = line[1].strip()
        payee = 'Anonimizado' if payee == 'Este concepto recoge las personas físicas cuya identidad queda protegida en cumplimiento de la Ley Organica de Protección de Datos' else payee

        # We got some anonymized entries
        anonymized = False
        anonymized = (True if payee == 'Anonimizado' else anonymized)

        # We got the description
        description = line[2].strip()

        # We got a localized amount (e.g. 42.732,08) sometimes including the currency symbol (e.g. 70.162,49 €)
        amount = re.sub(r'[^\d.,-]+', '', line[4])
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
