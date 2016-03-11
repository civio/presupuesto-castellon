# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class CastellonBudgetLoader(SimpleBudgetLoader):

    # An artifact of the in2csv conversion of the original XLS files is a trailing '.0', which we remove here
    def clean(self, s):
        return s.split('.')[0]

    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        programme_mapping = {
            # old programme: new programme
            '1340': '1350',
            '1350': '1360',
            '3130': '3110'
        }

        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)
        if is_expense:
            fc_code = self.clean(line[1]).zfill(5)      # Fill with zeroes on the left if needed
            ic_code = self.clean(line[0]).zfill(3)      # Fill with zeroes on the left if needed

            # We're sticking with the first three digits, i.e. groups of programmes,
            # because we don't have a proper list of programmes, the data is noisy.
            # Except in the case of policy 24 (Employment) where the client asked for more detail.
            if fc_code[:2] != '24':
                fc_code = fc_code[:3]+'0'

            # For years before 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)
            if year in ['2013', '2014']:
                new_programme = programme_mapping.get(fc_code)
                if new_programme:
                    fc_code = new_programme

            # For years before 2016 we check whether we need to amend the institutional code
            if year not in ['2013', '2014', '2015']:
                ic_code = '1'+ic_code[1:]

            return {
                'is_expense': True,
                'is_actual': is_actual,
                # After some tests and debate it was decided to use programs (i.e. 4 digit codes)
                # instead of subprograms (5 digits). So we keep just the first four digits.
                'fc_code': fc_code[:4],
                'ec_code': self.clean(line[2]),
                'ic_code': ic_code,
                'item_number': self.clean(line[2])[-2:],    # Last two digits
                'description': line[3],
                'amount': self._parse_amount(line[7 if is_actual else 4])
            }

        else:
            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': self.clean(line[1]),
                'ic_code': '999',                           # All income goes to the root node (999)
                'item_number': self.clean(line[1])[-2:],    # Last two digits
                'description': line[2],
                'amount': self._parse_amount(line[6 if is_actual else 3])
            }
