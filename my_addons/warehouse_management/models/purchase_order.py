from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    @api.constrains('partner_id', 'company_id')
    def _check_external_vendor_for_subsidiary(self):
        for order in self:
            # Kiểm tra nếu công ty hiện tại là công ty con
            company_partner = order.company_id.partner_id
            if company_partner.is_subsidiary and order.partner_id.is_external_vendor:
                raise ValidationError(_('Công ty con không được phép mua hàng từ nhà cung cấp ngoài!'))
    
    @api.onchange('partner_id')
    def _onchange_partner_warning(self):
        """Kiểm tra xem nhà cung cấp có phải là nhà cung cấp ngoài không"""
        if not self.partner_id:
            return
        
        # Kiểm tra xem công ty hiện tại có phải là công ty con không
        current_company = self.env.company
        if current_company.partner_id.is_subsidiary and self.partner_id.is_external_vendor:
            return {
                'warning': {
                    'title': _("Cảnh báo!"),
                    'message': _("Công ty con không được phép mua hàng từ nhà cung cấp ngoài.\n"
                                "Vui lòng chọn nhà cung cấp khác hoặc mua hàng thông qua công ty mẹ."),
                }
            } 