from django.contrib import admin
from .models import Location, RoutePlan, RouteStop

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'is_depot')
    list_filter = ('is_depot',)
    search_fields = ('name',)



class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1  # Số dòng trống mặc định để thêm nhanh điểm dừng
    ordering = ('stop_order',)


@admin.register(RoutePlan)
class RoutePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_distance', 'is_optimized', 'created_at')
    list_filter = ('is_optimized',)
    search_fields = ('name',)
    inlines = [RouteStopInline]

# Nếu cần quản lý rời rạc RouteStop (thường ít dùng vì đã có inline)
@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ('route', 'stop_order', 'location')
    list_filter = ('route',)
