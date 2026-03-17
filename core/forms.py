from django import forms


class CsvUploadForm(forms.Form):
    """
    Form upload file CSV địa điểm.
    - csv_file  : file .csv bắt buộc
    - import_mode: 'overwrite' (xóa cũ) hoặc 'append' (thêm mới)
    """
    csv_file = forms.FileField(
        label="Chọn file CSV",
        help_text="Chỉ chấp nhận file .csv",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"}),
    )

    IMPORT_CHOICES = [
        ("overwrite", "Ghi đè — xóa toàn bộ dữ liệu cũ rồi import mới"),
        ("append",    "Thêm mới — giữ dữ liệu cũ, chỉ thêm các điểm mới"),
    ]
    import_mode = forms.ChoiceField(
        label="Chế độ import",
        choices=IMPORT_CHOICES,
        widget=forms.RadioSelect,
        initial="overwrite",
    )

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        name = f.name.lower()
        if not name.endswith(".csv"):
            raise forms.ValidationError("File phải có đuôi .csv")
        if f.size == 0:
            raise forms.ValidationError("File không được rỗng.")
        return f
