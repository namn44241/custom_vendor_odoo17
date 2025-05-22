from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_confirm(self):
        for order in self:
            self._assign_nearest_warehouse(order)
        return super(SaleOrder, self).action_confirm()
    
    def action_assign_nearest_warehouse(self):
        """Phương thức public để gọi từ button"""
        for order in self:
            assigned_warehouses = self._assign_nearest_warehouse(order)
            if assigned_warehouses:
                # Hiển thị thông báo về các kho đã được chọn
                warehouse_names = ', '.join([w.name for w in assigned_warehouses])
                message = _("Đã chọn kho gần nhất cho đơn hàng: %s") % warehouse_names
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Thành công'),
                        'message': message,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cảnh báo'),
                        'message': _("Không tìm thấy kho phù hợp hoặc khách hàng không có tọa độ GPS."),
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        return True
    
    def _assign_nearest_warehouse(self, order):
        """Gán kho gần nhất có hàng cho từng dòng đơn hàng"""
        # Lấy vị trí khách hàng
        partner = order.partner_shipping_id or order.partner_id
        if not partner.latitude or not partner.longitude:
            return False
        
        # Tìm tất cả kho của công ty
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', order.company_id.id)
        ])
        
        if not warehouses:
            return False
        
        assigned_warehouses = set()
        
        for line in order.order_line:
            # Kiểm tra xem sản phẩm có cần quản lý kho không
            if line.product_id.type != 'product':
                continue
            
            # Tìm kho gần nhất có đủ hàng
            nearest_warehouse = False
            min_distance = float('inf')
            
            for warehouse in warehouses:
                # Kiểm tra tồn kho
                quant_sum = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id.warehouse_id', '=', warehouse.id),
                    ('location_id.usage', '=', 'internal'),
                ]).filtered(lambda q: q.quantity > 0)
                
                available_qty = sum(quant.quantity - quant.reserved_quantity for quant in quant_sum)
                
                if available_qty < line.product_uom_qty:
                    continue
                
                # Tính khoảng cách
                distance = warehouse.calculate_distance(
                    partner.latitude,
                    partner.longitude
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_warehouse = warehouse
            
            if nearest_warehouse:
                # Thêm vào danh sách kho đã chọn
                assigned_warehouses.add(nearest_warehouse)
                
                # Cập nhật warehouse_id cho dòng đơn hàng
                # Ở đây cần xác định đúng field để lưu, có thể cần điều chỉnh theo cấu trúc thực tế
                if hasattr(line, 'warehouse_id'):
                    line.warehouse_id = nearest_warehouse.id
                else:
                    # Thay thế bằng cách cập nhật route hoặc stock rule
                    route_ids = self.env['stock.route'].search([
                        ('warehouse_ids', 'in', nearest_warehouse.id)
                    ])
                    if route_ids:
                        line.route_id = route_ids[0].id
                
                # Thêm ghi chú về kho được chọn
                line.name = line.name + _("\n(Kho được chọn: %s)") % nearest_warehouse.name
        
        return list(assigned_warehouses) 