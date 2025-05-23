from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class WarehouseFinderWizard(models.TransientModel):
    _name = 'warehouse.finder.wizard'
    _description = 'Tìm kho phù hợp nhất có đủ hàng'
    
    sale_order_id = fields.Many2one('sale.order', string='Đơn hàng')
    found_warehouse_id = fields.Many2one('stock.warehouse', string='Kho được tìm thấy')
    message = fields.Text(string='Thông báo')
    has_warehouse = fields.Boolean(string='Có kho phù hợp', default=False)
    
    @api.model
    def default_get(self, fields_list):
        res = super(WarehouseFinderWizard, self).default_get(fields_list)
        
        active_id = self.env.context.get('active_id')
        if active_id:
            sale_order = self.env['sale.order'].browse(active_id)
            if sale_order:
                # Tìm kho phù hợp
                nearest_wh, available = sale_order._find_nearest_warehouse_with_stock()
                
                res['sale_order_id'] = sale_order.id
                if nearest_wh:
                    res['has_warehouse'] = True
                    res['found_warehouse_id'] = nearest_wh.id
                    
                    # Lấy state của kho để hiển thị
                    state_name = nearest_wh.company_id.partner_id.state_id.name or 'N/A'
                    
                    res['message'] = _('Đã tìm thấy kho phù hợp có đủ hàng: %s (tại %s)') % (nearest_wh.name, state_name)
                else:
                    res['has_warehouse'] = False
                    res['message'] = _('Không tìm thấy kho nào có đủ hàng cho đơn hàng này.')
        
        return res
    
    def action_confirm(self):
        """Áp dụng kho đã tìm thấy vào đơn hàng"""
        self.ensure_one()
        if self.found_warehouse_id and self.sale_order_id:
            # Cập nhật warehouse_id cho tất cả dòng đơn hàng
            for line in self.sale_order_id.order_line:
                if line.product_id.type == 'product':
                    line.warehouse_id = self.found_warehouse_id.id
            
            return {'type': 'ir.actions.act_window_close'}
        
    def action_cancel(self):
        """Đóng wizard mà không thực hiện hành động"""
        return {'type': 'ir.actions.act_window_close'} 