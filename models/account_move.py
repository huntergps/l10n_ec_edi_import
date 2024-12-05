from odoo import api, fields, models, Command, _

from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    edocument_id = fields.Many2one('edocument', string='Documento Electronico', copy=False)

    def all_in_one_force_delete_invoice_and_related_payment(self):
        """
        This method is used to find payment of invoices & get deleted & with that draft/posted invoice get deleted.
        """
        if not self._context.get('force_delete'):
            raise UserError(_("You cannot delete an invoice. something went wrong force delete context"))
        for invoice in self:
            related_payments_ids = invoice.matched_payment_ids
            if related_payments_ids:
                related_payments_ids.action_draft()
                related_payments_ids.write({'name': False})
                related_payments_ids.unlink()
        invoice_posted_cancel = self.filtered(lambda x: x.state in ['posted', 'cancel']) or self.env['account.move']
        invoice_draft = self.filtered(lambda x: x.state not in ['posted', 'cancel'])
        # draft invoice found in list view maybe
        if invoice_posted_cancel or invoice_draft:
            invoice_posted_cancel.button_draft()
            if not self._context.get('skip_unlink_records_invoice'):
                invoice_posted_cancel.with_context(force_delete=True).unlink()
                invoice_draft.with_context(force_delete=True).unlink()
            else:
                invoice_posted_cancel.button_cancel()
                invoice_draft.button_cancel()

    def all_in_one_bulk_cancel_invoice(self):
        """
        - This method is called when Cancel Invoice called from action of list view of invoices
        - From this method firstly system find that if any paid invoices then find payments & get unlinked,
        after that invoices get cancelled.
        """
        if self.filtered(lambda r: r.state == 'cancel'):
            raise ValidationError('One or many records are already cancelled.')
        for rec in self:
            rec.with_context(skip_unlink_records_invoice=True,
                             force_delete=True).all_in_one_force_delete_invoice_and_related_payment()



class AccountMoveLine(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = ['account.move.line']

    edocument_line_id = fields.Many2one('edocument.line', 'Linea Documento Electronico', ondelete='set null', index='btree_not_null', copy=False)
    edocument_order_id = fields.Many2one('edocument', 'Documento Electronico', related='edocument_line_id.document_id', readonly=True)

    def _copy_data_extend_business_fields(self, values):
        # OVERRIDE to copy the 'purchase_line_id' field as well.
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values['edocument_line_id'] = self.edocument_line_id.id
