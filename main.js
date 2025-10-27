// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flashed messages after 4 seconds
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.remove('show');
            alert.classList.add('fade');
        }, 4000);
    });

    // Autofocus the first input in any form on page load
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        var firstInput = form.querySelector('input[type="text"], input[type="email"], input[type="password"], input[type="number"]');
        if (firstInput) {
            firstInput.focus();
        }
    });

    // Example: AJAX booking form submission
    window.submitBookingForm = function(formId) {
        var form = document.getElementById(formId);
        var formData = new FormData(form);
        fetch(form.action, {
            method: form.method,
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            // Handle booking response here
            if (data.success) {
                alert('Booking successful!');
                window.location.reload();
            } else {
                alert('Booking failed: ' + data.error);
            }
        })
        .catch(error => {
            alert('Booking request failed: ' + error.message);
        });
    };

    // Example usage for dashboard stats via AJAX
    if (document.getElementById('dashboardStats')) {
        fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Render stats if needed, e.g. build charts with Chart.js
            // For now, you can log:
            console.log('Dashboard stats:', data);
        });
    }
});
