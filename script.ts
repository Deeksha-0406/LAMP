document.addEventListener('DOMContentLoaded', function() {
    // Handle laptop assignment form submission
    document.getElementById('assignLaptopForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const employeeName = document.getElementById('employeeName').value;

        fetch('/api/assignLaptop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ employeeName })
        })
        .then(response => response.text())
        .then(data => {
            console.log('Assign Laptop response:', data); // Debugging line
            document.getElementById('assignLaptopResult').innerText = data;
        })
        .catch(error => {
            console.error('Fetch error:', error); // Debugging line
            document.getElementById('assignLaptopResult').innerText = 'Error: ' + error;
        });
    });

    // Handle laptop reservation form submission
    document.getElementById('reserveLaptopForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const managerName = document.getElementById('managerName').value;
        const employeeName = document.getElementById('employeeNameReserve').value;
        const model = document.getElementById('model').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        fetch('/api/reserve_laptop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ managerName, employeeName, model, startDate, endDate })
        })
        .then(response => response.text())
        .then(data => {
            console.log('Reserve Laptop response:', data); // Debugging line
            document.getElementById('reserveLaptopResult').innerText = data;
        })
        .catch(error => {
            console.error('Fetch error:', error); // Debugging line
            document.getElementById('reserveLaptopResult').innerText = 'Error: ' + error;
        });
    });

    // Handle predict maintenance button click
    document.getElementById('predictMaintenanceButton').addEventListener('click', function() {
        fetch('/api/predictMaintenance')
        .then(response => response.json())
        .then(data => {
            console.log('Predict Maintenance response:', data); // Debugging line
            document.getElementById('predictMaintenanceResult').innerText = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            console.error('Fetch error:', error); // Debugging line
            document.getElementById('predictMaintenanceResult').innerText = 'Error: ' + error;
        });
    });

    // Handle employee onboarding form submission
    document.getElementById('onboardEmployeeForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const name = document.getElementById('name').value;
        const role = document.getElementById('role').value;
        const email = document.getElementById('email').value;
        const dateJoined = document.getElementById('dateJoined').value;

        fetch('/api/onboard_employee', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, role, email, dateJoined })
        })
        .then(response => response.text())
        .then(data => {
            console.log('Onboard Employee response:', data); // Debugging line
            document.getElementById('onboardEmployeeResult').innerText = data;
        })
        .catch(error => {
            console.error('Fetch error:', error); // Debugging line
            document.getElementById('onboardEmployeeResult').innerText = 'Error: ' + error;
        });
    });
});
