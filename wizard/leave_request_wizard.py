from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import io
import json
import xlsxwriter
from odoo.tools import date_utils


class LeaveRequestWizard(models.TransientModel):
    _name = 'leave.request.wizard'

    student_id = fields.Many2many('student.information', string='Student Name')
    room_id = fields.Many2one('room.management', string='Room')
    leave_date = fields.Date(string='Start Date')
    arrival_date = fields.Date(string='Arrival Date')
    student_ids = fields.Many2many('student.information',
                                   compute='compute_student_ids')

    @api.depends('room_id')
    def compute_student_ids(self):
        """function for dynamic domain,When choosing a room give
        corresponding students"""
        for rec in self:
            rec.student_ids = self.env["student.information"].search([]).ids
            if rec.room_id:
                student = rec.room_id.student_ids.ids
                rec.student_ids = student

    def _check_leave_date_arrival_date(self):
        """checking arrival date greater than leave date"""
        if self.leave_date and self.arrival_date:
            if self.leave_date > self.arrival_date:
                raise (ValidationError
                       ("Arrival Date must be greater than Start Date"))

    def action_print_leave_report(self):
        """function defined to print leave request report using psql query"""
        self._check_leave_date_arrival_date()
        query = """SELECT rm.name,si.name as std,lr.leave_date,lr.arrival_date,
        si.id,lr.duration
                    FROM leave_request lr   
                    INNER JOIN student_information si ON lr.student_name_id = 
                    si.id
                    INNER JOIN room_management rm ON si.room_id = rm.id
                    WHERE 1=1"""
        if self.student_id:
            students = tuple(self.student_id.ids)
            # query += (""" where rm.name = '%s'""" % self.room_id.name)
            if len(students) > 1:
                query += f""" and si.id in {students}"""
            else:
                query += (""" and si.id = '%s'""" % self.student_id.id)

        if self.room_id:
            query += (""" and lr.room_id =  '%s'""" % self.room_id.id)
        if self.leave_date:
            query += (""" and lr.leave_date = '%s'""" % self.leave_date)
        if self.arrival_date:
            query += (""" and lr.arrival_date =  '%s'""" % self.arrival_date)

        self.env.cr.execute(query)
        report = self.env.cr.dictfetchall()
        std = [std for std in report if 'student' not in std]
        count = 0
        if len(std) > 1:
            count = len(std)
        name = [name for name in report if 'room' not in name]
        counts = 0
        if len(name) > 1:
            counts = len(name)
            print('c', counts)
        data = {'report': report, 'count': count, 'counts': counts}
        print('data of leave', data)
        if report:
            return (self.env.ref(
                'hostel_management.action_leave_report').
                    report_action(self, data=data))

        else:
            raise UserError("No matching records...give correct values")

    def action_leave_report_excel(self):
        query = """SELECT rm.name,si.name as std,lr.leave_date,lr.arrival_date,
                            si.id,lr.duration
                            FROM leave_request lr   
                            INNER JOIN student_information si ON 
                            lr.student_name_id = si.id
                            INNER JOIN room_management rm ON si.room_id = rm.id
                            WHERE 1=1"""
        if self.student_id:
            students = tuple(self.student_id.ids)
            if len(students) > 1:
                query += f""" and si.id in {students}"""
            else:
                query += (""" and si.id = '%s'""" % self.student_id.id)

        if self.room_id:
            query += (""" and lr.room_id =  '%s'""" % self.room_id.id)
        if self.leave_date:
            query += (""" and lr.leave_date = '%s'""" % self.leave_date)
        if self.arrival_date:
            query += (
                    """ and lr.arrival_date =  '%s'""" % self.arrival_date)

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
        if report:
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'leave.request.wizard',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Leave Request Excel Report',
                         },
                'report_type': 'xlsx',
            }
        else:
            raise UserError("No matching records...give correct values")

    def get_xlsx_report(self, data, response):
        index = 1
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column('A:E', 18)
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px',
             'color': 'red'})
        txt_head = workbook.add_format({'font_size': '10px', 'align': 'center',
                                        })
        table_head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px', 'border': 1})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center',
                                   'border': 1})
        company_head = workbook.add_format({'font_size': '10px',
                                            'align': 'center', 'bold': True})
        sheet.merge_range('A2:E3', 'LEAVE REQUEST EXCEL REPORT', head)
        # std = [std for std in data['report'] if 'student' not in std]
        name = []
        for rec in data['report']:
            room = rec['name']
            if room not in name:
                name.append(room)
            print('name', name)
        table_row = 5
        for room in name:
            print('2', name)
            print('1', room)
            r1, r2 = table_row, table_row + 2
            sheet.merge_range('H2:K2', data['company']['name'], company_head)
            sheet.merge_range('H3:K3', data['company']['street'], company_head)
            sheet.merge_range('H4:K4', data['company']['city'], company_head)
            sheet.merge_range('H5:K5', data['company']['country'], company_head)
            sheet.write(f'A{r2}', 'SL No', table_head)
            sheet.write(f'A{table_row}', 'Room:', cell_format)
            sheet.write(f'B{r2}', 'Name', table_head)
            sheet.write(f'C{r2}', 'Start Time', table_head)
            sheet.write(f'D{r2}', 'Arrival Time', table_head)
            sheet.write(f'E{r2}', 'Duration', table_head)
            i = r2 + 1
            index = 1
            for rec in data.get('report', False):
                if rec.get('name') == room:
                    sheet.write(f'B{table_row}', rec['name'], txt_head)
                    sheet.write(f'A{i}', index, txt)
                    sheet.write(f'B{i}', rec['std'], txt)
                    sheet.write(f'C{i}', rec['leave_date'], txt)
                    sheet.write(f'D{i}', rec['arrival_date'], txt)
                    sheet.write(f'E{i}', rec['duration'], txt)
                    index = index + 1
                    i = i + 1
            table_row = i + 5
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
# if len(std) > 1:
        #     sheet.write('D5', 'SL No', table_head)
        #     sheet.write('E5', 'Name', table_head)
        #     sheet.write('F5', 'Room', table_head)
        #     sheet.write('G5', 'Start Time', table_head)
        #     sheet.write('H5', 'Arrival Time', table_head)
        #     sheet.write('I5', 'Duration', table_head)
        # else:
        #     sheet.write('D5', 'SL No', table_head)
        #     sheet.merge_range('B4:C4', 'Student:', cell_format)
        #     sheet.write('E5', 'Room', table_head)
        #     sheet.write('F5', 'Start Time', table_head)
        #     sheet.write('G5', 'Arrival Time', table_head)
        #     sheet.write('H5', 'Duration', table_head)
        #
        # for i, rec in enumerate(data['report'], start=6):
        #     if len(std) > 1:
        #         sheet.write(f'D{i}', index, txt)
        #         sheet.write(f'E{i}', rec['std'], txt)
        #         sheet.write(f'F{i}', rec['name'], txt)
        #         sheet.write(f'G{i}', rec['leave_date'], txt)
        #         sheet.write(f'H{i}', rec['arrival_date'], txt)
        #         sheet.write(f'I{i}', rec['duration'], txt)
        #         index = index + 1
        #     else:
        #         sheet.write(f'D{i}', index, txt)
        #         sheet.write('D4', rec['std'], txt)
        #         sheet.write(f'E{i}', rec['name'], txt)
        #         sheet.write(f'F{i}', rec['leave_date'], txt)
        #         sheet.write(f'G{i}', rec['arrival_date'], txt)
        #         sheet.write(f'H{i}', rec['duration'], txt)
        #         index = index + 1
