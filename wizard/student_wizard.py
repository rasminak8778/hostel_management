from odoo import fields, models, api
from odoo.exceptions import UserError
import io
import json
import xlsxwriter
from odoo.tools import date_utils


class StudentWizard(models.TransientModel):
    _name = 'student.wizard'

    room_id = fields.Many2one('room.management', string='Room')
    student_id = fields.Many2many('student.information',
                                  string='Students')
    alternate_ids = fields.Many2many('student.information',
                                     compute='compute_alternate_ids')

    @api.depends('room_id')
    def compute_alternate_ids(self):
        for rec in self:
            rec.alternate_ids = self.env["student.information"].search([]).ids
            print('rec.alternate_ids',rec.alternate_ids)
            if rec.room_id:
                student = rec.room_id.student_ids.ids
                rec.alternate_ids = student

    def action_print_student_report(self):
        """function defined to print student report using psql query"""
        query = """select si.name as std,si.amount,rm.name,si.id,
                        si.invoice_status
                        from student_information as si
                        inner join room_management as rm on rm.id = si.room_id
                        where true"""
        if self.room_id:
            query += (""" and si.room_id = '%s'""" % self.room_id.id)
        if self.student_id:
            students = tuple(self.student_id.ids)
            # query += (""" where rm.name = '%s'""" % self.room_id.name)
            if len(students) > 1:
                query += f""" and si.id in {students}"""
            else:
                query += (""" and si.id = '%s'""" % self.student_id.id)

        self.env.cr.execute(query)
        report = self.env.cr.dictfetchall()
        std = [std for std in report if 'student' not in std]
        count = 0
        if len(std) > 1:
            count = len(std)
        # name = [name for name in report if 'room' not in name]
        name = []
        for a in report:
            room = a['name']
            if room not in name:
                name.append(room)
        counts = 0
        if len(name) > 1:
            counts = len(name)
        if report:
            data = {'report': report, 'count': count, 'counts': counts}
            return (self.env.ref(
                'hostel_management.action_student_report').
                    report_action(self, data=data))
        else:
            raise UserError("No matching records are There")

    def action_student_report_excel(self):
        query = """select si.name as std,si.amount,rm.name,si.id,
                                si.invoice_status
                                from student_information as si
                                inner join room_management as rm on 
                                rm.id = si.room_id
                                where true"""
        if self.room_id:
            query += (""" and si.room_id = '%s'""" % self.room_id.id)
        if self.student_id:
            students = tuple(self.student_id.ids)
            if len(students) > 1:
                query += f""" and si.id in {students}"""
            else:
                query += (""" and si.id = '%s'""" % self.student_id.id)

        self.env.cr.execute(query)
        report = self.env.cr.dictfetchall()
        my_company = self.env.company
        company = {
            'name': my_company.name,
            'street': my_company.street,
            'city': my_company.city,
            'country': my_company.country_id.name
        }
        data = {'report': report,
                'company': company}
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'student.wizard',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Students Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column('A:E', 18)
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center', 'bold': True})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px',
             'color': 'red'})
        table_head = workbook.add_format(
            {'align': 'center', 'bold': True, 'border': 1, 'font_size': '10px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center',
                                   'border': 1})
        txt_head = workbook.add_format({'font_size': '10px', 'align': 'center'})
        company_head = workbook.add_format({'font_size': '10px',
                                            'align': 'center', 'bold': True})
        sheet.merge_range('A2:E3', 'STUDENTS EXCEL REPORT', head)
        name = []
        for rec in data['report']:
            room = rec['name']
            if room not in name:
                name.append(room)
            print('name', name)
        std = []
        for rec in data['report']:
            student = rec['std']
            if student not in std:
                std.append(student)
        table_row = 5
        table_row_2 = 6
        for room in name:
            print('2', name)
            r1, r2 = table_row, table_row + 2
            sheet.merge_range('H2:K2', data['company']['name'], company_head)
            sheet.merge_range('H3:K3', data['company']['street'], company_head)
            sheet.merge_range('H4:K4', data['company']['city'], company_head)
            sheet.merge_range('H5:K5', data['company']['country'], company_head)
            sheet.write(f'A{table_row}', 'Room:', cell_format)
            if len(std) == 1:
                sheet.write(f'B{r2}', 'SL No', table_head)
                sheet.write(f'A{table_row_2}', 'Name:', cell_format)
            else:
                sheet.write(f'A{r2}', 'SL No', table_head)
                sheet.write(f'B{r2}', 'Name', table_head)
            sheet.write(f'C{r2}', 'Pending Amount', table_head)
            sheet.write(f'D{r2}', 'Invoice Status', table_head)
            i = r2+1
            index = 1
            for rec in data.get('report', False):
                if rec.get('name') == room:
                    sheet.write(f'B{table_row}', rec['name'], txt_head)
                    print('l', std)
                    if len(std) == 1:
                        sheet.write(f'B{i}', index, txt)
                        sheet.write(f'B{table_row_2}', rec['std'], txt_head)
                    else:
                        sheet.write(f'A{i}', index, txt)
                        sheet.write(f'B{i}', rec['std'], txt)
                    sheet.write(f'C{i}', rec['amount'], txt)
                    sheet.write(f'D{i}', rec['invoice_status'], txt)
                    index = index + 1
                    i = i+1
            table_row = i+5
            table_row_2 = i+5
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


 # std = [std for std in report] if 'student' not in std]