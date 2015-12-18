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
        # Skip lines without the first element
        if line[0] == '':
            return {
                'amount': 0
            }

        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        programme_mapping = {
            # old programme: new programme
            '1332': '1330',     # TRAFICO
            '1330': '1340',     # SECC.MOVILIDAD URBANA
            '1331': '1341',     # UNID.ADMIN.MOVILIDAD URBANA
            '1331': '1333',     # UNID.TECN.MOV.URBANA
            '1512': '1511',     # SEC.CONTROL URBANISTICO
            '1550': '1530',     # SECCION INFRA. SS PP Y M.A.
            '1554': '1533',     # BRIGADAS MUNICIPALES
            '1553': '1535',     # CONSERVACION
            '1551': '1537',     # NEG.ADMIN.INFRAESTRUCTURAS
            '1790': '1722',     # PROYECTOS EUROPEOS
            '2301': '2310',     # SECCION SERV.SOCIALES Y CULTURALES
            '2322': '2311',     # DINAMIZACION COMUNITARIA
            '3130': '3110',     # SANIDAD
            '3320': '3321',     # BIBLIOTECAS
            '3350': '3342',     # BANDA MUSICA
            '4410': '4411',     # TRANSPORTE PUBLICO
            '1552': '9203',     # INGENIERIA
            '9230': '9231',     # ESTADISTICA
        }

        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)
        if is_expense:
            fc_code = self.clean(line[1]).zfill(4)          # Fill with zeroes on the left if needed
            ic_code = self.clean(line[0]).zfill(3)          # Fill with zeroes on the left if needed

            # Remove last char to fc_code if grather than 4 chars
            if len(fc_code) == 5:
                fc_code = fc_code[:-1]

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
                'fc_code': fc_code,
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
