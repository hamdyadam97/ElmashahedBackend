/**
 * قوالب PDF جاهزة للأذونات
 * Presets for Permission PDF Templates
 */

const TEMPLATE_PRESETS = {
    tvtc: {
        name: "📘 قالب TVTC الرسمي",
        header: `<div style="text-align: center; border-bottom: 3px solid #1e3a8a; padding-bottom: 15px; margin-bottom: 20px;">
    <img src="data:image/png;base64,{{ vision_logo }}" style="width: 80px; float: left; margin-left: 20px;">
    <img src="data:image/png;base64,{{ tvtc_logo }}" style="width: 80px; float: right; margin-right: 20px;">
    <div style="clear: both;"></div>
    <h2 style="color: #1e3a8a; margin: 10px 0; font-size: 22px;">{{ institute.name }}</h2>
    <p style="color: #666; margin: 5px 0;">رقم الترخيص: {{ institute.license_number }}</p>
    <div style="background: #1e3a8a; color: white; padding: 8px; margin-top: 10px; font-size: 18px; font-weight: bold;">
        إذن دراسة رسمي - Official Study Permission
    </div>
</div>`,
        body: `<div style="border: 2px solid #1e3a8a; padding: 20px; margin: 15px 0; border-radius: 5px;">
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #e0e7ff;">
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold; width: 30%;">رقم الإذن</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ permission.permission_number }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold;">اسم الطالب</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ client.full_name }}</td>
        </tr>
        <tr style="background: #f8fafc;">
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold;">رقم الهوية</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ client.national_id }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold;">البرنامج</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ program.name }}</td>
        </tr>
        <tr style="background: #f8fafc;">
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold;">تاريخ البداية</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ program.start_date }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold;">تاريخ الانتهاء</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ program.end_date }}</td>
        </tr>
        <tr style="background: #f8fafc;">
            <td style="padding: 10px; border: 1px solid #1e3a8a; font-weight: bold;">مدة البرنامج</td>
            <td style="padding: 10px; border: 1px solid #1e3a8a;">{{ program.duration_months }} شهر</td>
        </tr>
    </table>
</div>`,
        footer: `<div style="margin-top: 40px; display: flex; justify-content: space-between; align-items: flex-end;">
    <div style="text-align: center; width: 45%;">
        <p style="font-weight: bold; margin-bottom: 5px;">توقيع الموظف المختص</p>
        <p style="margin-top: 30px; border-top: 1px solid #333; padding-top: 5px;">{{ issued_by.get_full_name }}</p>
        <p style="color: #666; font-size: 12px;">تاريخ الإصدار: {{ today }}</p>
    </div>
    <div style="text-align: center; width: 45%;">
        <p style="font-weight: bold; margin-bottom: 5px;">ختم المعهد</p>
        {% if institute.stamp_image %}
        <img src="file://{{ institute.stamp_image.path }}" style="width: 100px; margin-top: 10px;">
        {% else %}
        <div style="width: 100px; height: 100px; border: 2px dashed #ccc; margin: 10px auto; line-height: 100px; color: #999;">الختم</div>
        {% endif %}
    </div>
</div>
<div style="text-align: center; margin-top: 30px; font-size: 11px; color: #666; border-top: 1px solid #ddd; padding-top: 10px;">
    {{ institute.address }} - هاتف: {{ institute.phone }}
</div>`,
        css: `.page-container { font-family: 'Arial', sans-serif; direction: rtl; padding: 10px; }
table td { font-size: 14px; }`,
        page_size: 'A4',
        orientation: 'portrait'
    },

    simple: {
        name: "📄 قالب بسيط نظيف",
        header: `<div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #ddd;">
    {% if institute.logo %}
    <img src="file://{{ institute.logo.path }}" style="max-width: 100px; max-height: 100px; margin-bottom: 10px;">
    {% endif %}
    <h2 style="color: #333; margin: 5px 0; font-size: 22px;">{{ institute.name }}</h2>
    <p style="color: #888; margin: 3px 0; font-size: 13px;">{{ institute.address }} | {{ institute.phone }}</p>
    <p style="color: #888; margin: 3px 0; font-size: 13px;">رقم الترخيص: {{ institute.license_number }}</p>
    <h3 style="color: #c53030; margin-top: 15px; font-size: 20px;">إذن دراسة</h3>
    <p style="color: #666; font-size: 12px;">رقم الإذن: <strong>{{ permission.permission_number }}</strong></p>
</div>`,
        body: `<div style="padding: 20px 0;">
    <div style="margin-bottom: 20px;">
        <h4 style="color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px;">👤 بيانات الطالب</h4>
        <p style="margin: 8px 0;"><strong>الاسم:</strong> {{ client.full_name }}</p>
        <p style="margin: 8px 0;"><strong>رقم الهوية:</strong> {{ client.national_id }}</p>
        <p style="margin: 8px 0;"><strong>الهاتف:</strong> {{ client.phone }}</p>
        <p style="margin: 8px 0;"><strong>العنوان:</strong> {{ client.address }}</p>
    </div>
    <div style="margin-bottom: 20px;">
        <h4 style="color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px;">📚 بيانات البرنامج</h4>
        <p style="margin: 8px 0;"><strong>البرنامج:</strong> {{ program.name }}</p>
        <p style="margin: 8px 0;"><strong>النوع:</strong> {% if permission.diploma %}دبلومة ({{ program.duration_months }} شهر){% else %}دورة تدريبية ({{ program.duration_months }} شهر){% endif %}</p>
        <p style="margin: 8px 0;"><strong>تاريخ البداية:</strong> {{ program.start_date }}</p>
        <p style="margin: 8px 0;"><strong>تاريخ الانتهاء:</strong> {{ program.end_date }}</p>
    </div>
    <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; border-right: 4px solid #c53030;">
        <p style="margin: 0; color: #555; line-height: 1.8;">
            يُصرح للطالب المذكور أعلاه بالدراسة في البرنامج التدريبي المحدد، 
            وهذا الإذن صالح من تاريخ الإصدار وحتى تاريخ انتهاء البرنامج.
        </p>
    </div>
</div>`,
        footer: `<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; display: flex; justify-content: space-between;">
    <div>
        <p style="margin: 0; color: #666; font-size: 13px;">تم الإصدار بواسطة:</p>
        <p style="margin: 5px 0 0; font-weight: bold; color: #333;">{{ issued_by.get_full_name }}</p>
        <p style="margin: 3px 0 0; color: #999; font-size: 12px;">{{ today }}</p>
    </div>
    <div style="text-align: center;">
        {% if institute.stamp_image %}
        <img src="file://{{ institute.stamp_image.path }}" style="width: 80px; opacity: 0.8;">
        {% else %}
        <div style="width: 80px; height: 80px; border: 1px dashed #ccc; line-height: 80px; color: #bbb; font-size: 12px;">ختم المعهد</div>
        {% endif %}
    </div>
</div>`,
        css: `.page-container { font-family: 'Arial', sans-serif; direction: rtl; color: #333; line-height: 1.6; }
body { padding: 20px; }`,
        page_size: 'A4',
        orientation: 'portrait'
    }
};

function loadPreset(presetKey) {
    const preset = TEMPLATE_PRESETS[presetKey];
    if (!preset) return;

    const headerField = document.getElementById('id_header_content');
    const bodyField = document.getElementById('id_body_content');
    const footerField = document.getElementById('id_footer_content');
    const cssField = document.getElementById('id_custom_css');
    const pageSizeField = document.getElementById('id_page_size');
    const orientationField = document.getElementById('id_orientation');

    if (headerField) headerField.value = preset.header;
    if (bodyField) bodyField.value = preset.body;
    if (footerField) footerField.value = preset.footer;
    if (cssField) cssField.value = preset.css;
    if (pageSizeField) pageSizeField.value = preset.page_size;
    if (orientationField) orientationField.value = preset.orientation;

    // Update CodeMirror if exists
    if (window.headerCM) window.headerCM.setValue(preset.header);
    if (window.bodyCM) window.bodyCM.setValue(preset.body);
    if (window.footerCM) window.footerCM.setValue(preset.footer);
    if (window.cssCM) window.cssCM.setValue(preset.css);
}

document.addEventListener('DOMContentLoaded', function() {
    const presetContainer = document.getElementById('preset-buttons');
    if (!presetContainer) return;

    presetContainer.innerHTML = `
        <div class="alert alert-info mb-3">
            <i class="fas fa-lightbulb me-2"></i>
            <strong>اختصار:</strong> اختار قالب جاهز يملى الحقول تلقائياً، أو اكتب HTML/CSS يدوياً
        </div>
        <div class="d-flex gap-2 flex-wrap mb-3">
            ${Object.entries(TEMPLATE_PRESETS).map(([key, preset]) => `
                <button type="button" class="btn btn-outline-primary" onclick="loadPreset('${key}')">
                    <i class="fas fa-magic me-1"></i>${preset.name}
                </button>
            `).join('')}
        </div>
    `;
});
