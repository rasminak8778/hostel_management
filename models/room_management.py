# -*- coding: utf-8 -*-
from odoo import fields, models, api, Command


class RoomManagement(models.Model):
    """create and manage rooms"""
    _name = 'room.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Room Management'
    _rec_name = "name"

    name = fields.Char(string='Name', required=True, readonly=True,
                       default='New', index=True)
    room_type = fields.Selection(selection=[('ac_room', 'AC Room'),
                                            ('normal', 'Normal Room'),
                                            ('mattress', 'Mattress')],
                                 required=True)
    no_of_bed = fields.Integer(string='Number of Beds', default='1',
                               help='Give the number of beds that you want')
    rent = fields.Monetary(string='Rent', required=True, tracking=True)
    state = fields.Selection(selection=[('empty', 'Empty'), ('partial',
                                        'Partial'),
                                        ('full', 'Full'), ('cleaning',
                                        'Cleaning')], default='empty',
                             tracking=True)
    company_id = fields.Many2one('res.company', copy=False,
                                 default=lambda self: self.env.user.company_id.
                                 id)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id', store=True)
    occupied_bed_no = fields.Integer(string='Occupied',
                                     compute='_compute_occupied_bed')
    facilities_ids = fields.Many2many('hostel.facilities',
                                      string='Facilities')
    student_ids = fields.One2many('student.information',
                                  "room_id", string="Student Details")
    std_count = fields.Integer(string="Student count",
                               compute='_compute_std_count')
    monthly_amount = fields.Float(string="Total Amount",
                                  compute='_compute_monthly_amount', store=True)
    pending_amount = fields.Float(string='Pending Amount',
                                  compute='_compute_pending_amount')
    total_rent = fields.Float(compute="_compute_total_rent",
                              string="Total Rent")
    room_img = fields.Image()
    available_bed = fields.Integer(string="Available Bed",
                                   compute="_compute_available_bed")


    @api.model
    def create(self, vals):
        """"function defined to set unique room number"""
        vals['name'] = (self.env['ir.sequence']
                        .next_by_code('room.management'))
        return super(RoomManagement, self).create(vals)

    @api.depends('occupied_bed_no')
    def _compute_occupied_bed(self):
        for rec in self:
            rec.occupied_bed_no += rec.std_count
            print('occupied', rec.occupied_bed_no)
            if rec.occupied_bed_no == rec.no_of_bed:
                rec.write({
                    'state': 'full'
                })
            if rec.occupied_bed_no == 0:
                rec.write({
                    'state': 'empty'
                })
            if 0 < rec.occupied_bed_no < rec.no_of_bed:
                rec.write({
                    'state': 'partial'
                })

    def _compute_available_bed(self):
        """function for compute available bed"""
        for rec in self:
            rec.available_bed = (rec.no_of_bed - rec.occupied_bed_no)

    def _compute_std_count(self):
        """"function defined to compute std count"""
        for rec in self:
            rec.std_count = (self.env['student.information'].
                             search_count([('room_id', '=', rec.id)]))
            print('r',rec.std_count)
            # print(self)

    @api.depends('rent', 'facilities_ids.charge', 'no_of_bed')
    def _compute_monthly_amount(self):
        """"function defined to compute monthly amount of room"""
        for room in self:
            if room.no_of_bed != 0:
                room.monthly_amount = (room.rent +
                                       sum(room.facilities_ids.
                                           mapped('charge'))) / room.no_of_bed
            else:
                room.monthly_amount = 0

    def _compute_pending_amount(self):
        total_pending_amount = 0
        for student in self.student_ids:
            invoice = self.env['account.move'].search([
                ('partner_id',  '=', student.partner_id.id),
                ('payment_state', 'not in', ['paid']),
                ('move_type', '=', 'out_invoice')
            ])
            for rec in invoice:
                amount = rec.amount_total_signed
                total_pending_amount += amount
                print('a',total_pending_amount)
        self.pending_amount = total_pending_amount


    def action_generate_room_invoice(self):
        """function defined for generate room invoice by
        clicking invoice button"""
        students = self.student_ids
        for record in students:
            invoice = record.env['account.move']
            invoice.create({
                'move_type': 'out_invoice',
                'partner_id': record.partner_id.id,
                'room_student_name': record.id,
                'invoice_line_ids': [
                    Command.create({
                        'product_id': record.env.
                        ref('hostel_management.product_service').id,
                        'quantity': 1,
                        'price_unit': record.amount
                    })
                ]
            })

    def _compute_total_rent(self):
        """function defined for compute total rent of room """
        for room in self:
            room.total_rent = (room.rent +
                               sum(room.facilities_ids.mapped('charge')))
            print('mapped', room.total_rent)





    # @api.depends('student_ids')
    # def _compute_pending_amount(self):
    #     """function defined for compute pending amount"""
    #     # print('a',self)
    #     for record in self:
    #         drafted_invoices = self.student_ids.filtered(
    #             lambda i: i.invoice_status == 'pending')
    #         record.pending_amount = sum(drafted_invoices.mapped('amount'))
