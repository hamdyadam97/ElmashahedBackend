document.addEventListener('DOMContentLoaded', function() {
    // إنشاء عنصر iframe للمعاينة
    const previewContainer = document.createElement('div');
    previewContainer.innerHTML = `
        <h3 style="margin-top: 20px;">معاينة حية (Live Preview)</h3>
        <iframe id="pdf-preview" style="width: 100%; height: 500px; border: 1px solid #ccc; background: white;"></iframe>
    `;

    // إضافته في نهاية الفورم
    const adminForm = document.getElementById('permissiontemplate_form');
    if (adminForm) {
        adminForm.appendChild(previewContainer);

        const headerArea = document.querySelector('textarea[name="header_content"]');
        const bodyArea = document.querySelector('textarea[name="body_content"]');
        const footerArea = document.querySelector('textarea[name="footer_content"]');
        const cssArea = document.querySelector('textarea[name="custom_css"]');

        function updatePreview() {
            const iframe = document.getElementById('pdf-preview');
            const doc = iframe.contentDocument || iframe.contentWindow.document;

            // بيانات تجريبية للمعاينة (Dummy Data)
            const htmlContent = `
                <html dir="rtl">
                    <head>
                        <style>
                            body { font-family: sans-serif; margin: 10px; }
                            ${cssArea.value}
                        </style>
                    </head>
                    <body>
                        <header style="border-bottom:1px solid #eee">${headerArea.value}</header>
                        <main style="padding: 20px 0;">${bodyArea.value}</main>
                        <footer style="border-top:1px solid #eee; margin-top:20px;">${footerArea.value}</footer>
                        <hr>
                        <small style="color:red">ملاحظة: المتغيرات مثل {{ client.full_name }} ستظهر كقيم حقيقية عند إصدار الإذن الفعلي.</small>
                    </body>
                </html>
            `;

            doc.open();
            doc.write(htmlContent);
            doc.close();
        }

        // تحديث المعاينة عند الكتابة
        [headerArea, bodyArea, footerArea, cssArea].forEach(el => {
            el.addEventListener('input', updatePreview);
        });

        // تشغيل المعاينة لأول مرة
        updatePreview();
    }
});