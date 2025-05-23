from odoo import api, fields, models
import math

class ResCountryStatePosition(models.Model):
    _name = 'res.country.state.position'
    _description = 'Vị trí tọa độ của tỉnh/thành phố'
    
    name = fields.Char(string='Tên', required=True)
    state_code = fields.Char(string='Mã tỉnh', required=True, index=True)
    longitude = fields.Float(string='Kinh độ', digits=(16, 6), required=True)
    latitude = fields.Float(string='Vĩ độ', digits=(16, 6))
    
    _sql_constraints = [
        ('state_code_unique', 'unique(state_code)', 'Mỗi mã tỉnh chỉ được đăng ký một lần!')
    ]
    
    @api.model
    def calculate_distance(self, state_code1, state_code2):
        """Tính khoảng cách giữa hai tỉnh/thành phố dựa trên cả kinh độ và vĩ độ"""
        if not state_code1 or not state_code2:
            return 9999
            
        pos1 = self.search([('state_code', '=', state_code1)], limit=1)
        pos2 = self.search([('state_code', '=', state_code2)], limit=1)
        
        if not pos1 or not pos2:
            return 9999
        
        # Xử lý trường hợp cùng mã tỉnh
        if state_code1 == state_code2:
            return 0
            
        # Tính khoảng cách theo công thức Haversine đơn giản hóa
        # Khi ở cùng một quốc gia, chúng ta có thể sử dụng cách tính đơn giản hơn
        lat_diff = abs(pos1.latitude - pos2.latitude)
        long_diff = abs(pos1.longitude - pos2.longitude)
        
        # Sử dụng Euclidean distance (đơn giản hóa)
        distance = math.sqrt(lat_diff * lat_diff + long_diff * long_diff)
        
        return distance 