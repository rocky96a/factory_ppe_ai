async function loadDashboard() {

    try {

        const response =
            await fetch("/api/dashboard");

        const data =
            await response.json();

        document.getElementById(
            "cameraCount"
        ).textContent =
            data.camera_count;

        document.getElementById(
            "violationCount"
        ).textContent =
            data.violation_count;

        const container =
            document.getElementById(
                "cameraGrid"
            );

        container.innerHTML = "";

        const camerasResponse =
            await fetch("/api/cameras");

        const camerasData =
            await camerasResponse.json();

        camerasData.cameras.forEach(
            camera => {

                container.innerHTML += `

                    <div class="camera-card">

                        <img
                            src="/video/${camera.camera_id}"
                            alt="${camera.name}"
                        >

                        <div class="camera-info">

                            <strong>
                                ${camera.camera_id}
                            </strong>

                            <br>

                            ${camera.name}

                            <br>

                            ${camera.location}

                        </div>

                    </div>

                `;

            }
        );


        const violations =
            document.getElementById(
                "violations"
            );

        violations.innerHTML = "";

        data.recent_violations.forEach(
            violation => {

                violations.innerHTML += `

                    <div class="card">

                        <strong>
                            🚨 NO HELMET
                        </strong>

                        <br>

                        Camera:
                        ${violation.camera_id}

                        <br>

                        Location:
                        ${violation.location}

                        <br>

                        Worker ID:
                        ${violation.tracking_id}

                        <br>

                        Confidence:
                        ${(violation.confidence * 100)
                            .toFixed(1)}%

                        <br>

                        Time:
                        ${violation.timestamp}

                    </div>

                `;

            }
        );

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }
}


loadDashboard();


setInterval(
    loadDashboard,
    5000
);