async function recommendLaptop() {
    const employeeName = document.getElementById('employeeName').value;
    const resultDiv = document.getElementById('recommendationResult');

    if (!employeeName) {
        resultDiv.innerText = 'Employee name is required.';
        return;
    }

    try {
        const response = await fetch('/api/recommend_laptop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: employeeName })
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `
                <p>${data.message}</p>
                ${data.laptop ? `
                    <p><strong>Recommended Laptop Details:</strong></p>
                    <p>Model: ${data.laptop.model}</p>
                    <p>Serial Number: ${data.laptop.serialNumber}</p>
                    <p>Location: ${data.laptop.location}</p>
                    <p>Last Serviced: ${data.laptop.lastServiced}</p>
                ` : ''}
            `;
        } else {
            resultDiv.innerText = 'Error: ' + data.error;
        }
    } catch (error) {
        resultDiv.innerText = 'Error: ' + error.message;
    }
}

async function reserveLaptop() {
    const managerName = document.getElementById('reserveManagerName').value;
    const employeeName = document.getElementById('reserveEmployeeName').value;
    const model = document.getElementById('reserveModel').value;
    const startDate = document.getElementById('reserveStartDate').value;
    const endDate = document.getElementById('reserveEndDate').value;
    const resultDiv = document.getElementById('reservationResult');

    if (!managerName || !employeeName || !model || !startDate || !endDate) {
        resultDiv.innerText = 'All fields are required.';
        return;
    }

    try {
        const response = await fetch('/api/reserve_laptop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ manager_name: managerName, employee_name: employeeName, model: model, start_date: startDate, end_date: endDate })
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `<p>${data.message}</p>`;
        } else {
            resultDiv.innerText = 'Error: ' + data.error;
        }
    } catch (error) {
        resultDiv.innerText = 'Error: ' + error.message;
    }
}

async function onboardEmployee() {
    const name = document.getElementById('onboardName').value;
    const role = document.getElementById('onboardRole').value;
    const email = document.getElementById('onboardEmail').value;
    const dateJoined = document.getElementById('onboardDateJoined').value;
    const resultDiv = document.getElementById('onboardingResult');

    if (!name || !role || !email || !dateJoined) {
        resultDiv.innerText = 'All fields are required.';
        return;
    }

    try {
        const response = await fetch('/api/onboard_employee', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name, role: role, email: email, dateJoined: dateJoined })
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `<p>${data.message}</p>`;
        } else {
            resultDiv.innerText = 'Error: ' + data.error;
        }
    } catch (error) {
        resultDiv.innerText = 'Error: ' + error.message;
    }
}
