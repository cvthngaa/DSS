from django.db import models

class Location(models.Model):
    """
    Lưu trữ điểm giao hàng hoặc Kho xuất phát.
    Có tọa độ thật: latitude, longitude để hiển thị trên bản đồ.
    [DSS] → Thuộc phân hệ Data Management.
    """
    name = models.CharField(max_length=100, help_text="Tên điểm giao hàng hoặc Kho")
    
    # Tọa độ bản đồ thực tế
    latitude = models.FloatField(default=0.0, help_text="Vĩ độ (latitude) - tọa độ bắc/nam")
    longitude = models.FloatField(default=0.0, help_text="Kinh độ (longitude) - tọa độ đông/tây")
    
    is_depot = models.BooleanField(default=False, help_text="Đánh dấu đây là điểm xuất phát (Kho)")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['-is_depot', 'name'] # Kho luôn hiển thị trước, rồi mới tới KH

    def __str__(self):
        type_label = "[Kho]" if self.is_depot else "[KH]"
        return f"{type_label} {self.name} ({self.latitude:.4f}, {self.longitude:.4f})"


class RoutePlan(models.Model):
    """
    Đại diện cho 1 lần lưu tuyến đường (có thể là tuyến ban đầu hoặc tuyến tối ưu).
    """
    name = models.CharField(max_length=200, help_text="Tên hoặc mô tả tuyến đường")
    total_distance = models.FloatField(default=0.0, help_text="Tổng khoảng cách của tuyến")
    is_optimized = models.BooleanField(default=False, help_text="Đánh dấu tuyến này là kết quả từ thuật toán TSP")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Tối ưu" if self.is_optimized else "Ban đầu"
        return f"{self.name} - {status} ({self.total_distance:.2f} km)"


class RouteStop(models.Model):
    """
    Bảng trung gian để biết một Route (tuyến) đi qua những Location (điểm) nào,
    và theo thứ tự nào (stop_order).
    """
    route = models.ForeignKey(RoutePlan, on_delete=models.CASCADE, related_name='stops')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    stop_order = models.IntegerField(help_text="Thứ tự dừng của điểm này trong tuyến")

    class Meta:
        ordering = ['stop_order'] # Mặc định luôn sắp xếp theo thứ tự ghé thăm

    def __str__(self):
        return f"Tuyến {self.route.id} - Dừng {self.stop_order}: {self.location.name}"
