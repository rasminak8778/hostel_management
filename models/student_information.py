# -*- coding: utf-8 -*-
from odoo import fields, models, api, Command
from odoo.exceptions import ValidationError
from datetime import timedelta


class StudentInformation(models.Model):
    """add student information details"""
    _name = 'student.information'
    _description = 'Student Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "student"

    name = fields.Char(string='Name', required=True, help='Provide your name')
    student = fields.Char(string='Student ID', required=True,
                          readonly=True, default='New')
    dob = fields.Date(string='DOB', required=True)
    age = fields.Char(string="Age", compute="_compute_student",
                      store=True)
    room_id = fields.Many2one('room.management', string='Room',
                              tracking=True,  readonly=True)
    email = fields.Char(string='Email', help='Provide your personal Email',
                        required=True)
    image = fields.Image()
    address = fields.Text(string='Address')
    street = fields.Char(string='Street', help="mention your address")
    city = fields.Char(string='City', help="mention your City")
    state_id = fields.Many2one('res.country.state', string='State',
                               help="mention your State")
    zip = fields.Char(string='Zip', help="mention your Zip Code")
    country_id = fields.Many2one('res.country',
                                 help="mention your Country", string='Country')
    receive_mail = fields.Boolean(string='Receive Mail', default=False)
    company_id = fields.Many2one('res.company',
                                 store=True, copy=False,
                                 default=lambda self: self.env.user.company_id.
                                 id)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help='Partner for the student', readonly=True)
    available_room = fields.Char()
    active = fields.Boolean(default=True, tracking=True)
    invoice_status = fields.Selection(selection=[('pending', 'Pending'),
                                                 ('done', 'Done')],
                                      compute='_compute_invoice_state',store=True,
                                      default='pending', tracking=True)

    amount = fields.Float(string='Monthly Amount',
                          related='room_id.monthly_amount', store=True)
    user_id = fields.Many2one('res.users', string="user",
                              readonly=True)
    leave_request_ids = fields.One2many('leave.request',
                                        'student_name_id',
                                        string='Leave Request')
    invoice_count = fields.Integer(string='Invoice Count',
                                   compute='_compute_invoice_count')

    @api.model
    def create(self, vals):
        """function defined for student unique no and
        create a partner record in contact module"""
        vals['student'] = (self.env['ir.sequence'].
                           next_by_code('student.information'))

        student = super(StudentInformation, self).create(vals)
        # print('gh', vals)
        partner_values = {
            'name': student.name,
            'email': student.email,
        }
        partner = self.env['res.partner'].create(partner_values)
        student.write({'partner_id': partner.id})
        return student

    def action_alot_button(self):
        """function to defined for alot room which will alot the room for
         student. first check state full or empty  Update the state of the
          room accordingly"""
        available_room = self.env['room.management'].search(
            [('state', '!=', 'full')])
        if len(available_room) == 0:
            raise ValidationError("All the rooms are Full")
        self.room_id = available_room[0]

    @api.depends('dob')
    def _compute_student(self):
        # print( self.search([]))
        """function defined for automatically update the age based on dob"""
        today_date = fields.Datetime.today()
        for std in self:
            if std.dob:
                dob = fields.Datetime.to_datetime(std.dob)
                total_age = str(int((today_date - dob).days / 365))
                std.age = total_age
            else:
                std.age = False

    def action_vacate(self):
        """function is defined for vacate std based on time """
        current_time = fields.Datetime.now()
        start_time = current_time + timedelta(
            hours=4)
        self.write({'active': False})
        room_total = len(self.room_id.student_ids)
        if room_total == 0:
            cleaning_request_values = {
                'room_id': self.room_id.id,
                'start_time': start_time,
            }
            self.env['cleaning.service'].create(cleaning_request_values)
            self.room_id.update({'state': 'cleaning'})

    def generate_user(self):
        """function is defined for generate user  through automated action"""
        user_values = {
            'partner_id': self.partner_id.id,
            'login': self.email,
        }
        print(user_values)
        user = self.env['res.users'].create(user_values)
        self.write({'user_id': user.id})

    def generate_invoices(self):
        """function to create invoice generate invoices
        through scheduled action or automatically"""
        students = self.search([('active', '=', True)])

        for record in students:
            invoice = record.env['account.move']
            a = invoice.create({
                'move_type': 'out_invoice',
                'partner_id': record.partner_id.id,
                'invoice_line_ids': [
                    Command.create({
                        'product_id': record.env.
                        ref('hostel_management.product_service').id,
                        'quantity': 1,
                        'tax_ids': False,
                        'price_unit': record.amount
                    })
                ]
            })
            print('q', a)
            self.send_invoice_email(record)

    def send_invoice_email(self, record):
        """function is defined for send invoice through email """
        template = (self.env.
                    ref("hostel_management.student_invoice_email_template"))
        template.send_mail(record.id, force_send=True)

    def _compute_invoice_state(self):
        """function is defined for compute invoice state"""
        for record in self:
            unpaid_invoice = self.env['account.move'].search_count([
                ('payment_state', 'not in', ['paid']),
                ('move_type', '=', 'out_invoice'),
                ('partner_id', '=', record.partner_id.id)
            ])
            if unpaid_invoice == 0:
                self.write({'invoice_status': 'done'})
            else:
                self.write({'invoice_status': 'pending'})

    def unlink(self):
        """function is defined for delete leave requests when
        student leaving the room"""
        leave_requests = self.leave_request_ids
        leave_requests.unlink()
        return super(StudentInformation, self).unlink()

    def action_view_invoice(self):
        """function is defined for view_invoice in smart
        button tree and form views """
        self.ensure_one()
        print(len(self))
        print(self)
        inv = (self.env['account.move'].search([('partner_id', '=',
                                                 self.partner_id.id)]))
        if len(inv) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice for student',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': inv.id,
                'context': {
                    'default_partner_id': self.partner_id.id,
                    'default_move_type': 'out_invoice',

                }
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice for student',
                'view_mode': 'tree',
                'res_model': 'account.move',
                'domain': [('id', 'in', inv.ids)],
                'context': {
                    'default_partner_id': self.partner_id.id,
                    'default_move_type': 'out_invoice',

                }
            }

    def _compute_invoice_count(self):
        """function is defined for compute invoice count """
        for record in self:
            record.invoice_count = (self.env['account.move'].
                                    search_count([('partner_id', '=',
                                                   self.partner_id.id)]))







# self.room_id.occupied_bed_no += 1
        # if self.room_id.occupied_bed_no == self.room_id.no_of_bed:
        #     self.room_id.write({
        #         'state': 'full'
        #     })
        # if self.room_id.occupied_bed_no == 0:
        #     self.room_id.write({
        #         'state': 'new'
        #     })
        # if 0 < self.room_id.occupied_bed_no < self.room_id.no_of_bed:
        #     self.room_id.write({
        #         'state': 'partial'
        #     })
