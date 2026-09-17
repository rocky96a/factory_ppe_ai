let browserStream = null;


// ============================================================
// BROWSER CAMERA
// ============================================================

async function startBrowserCamera() {

    const video =
        document.getElementById("browserCamera");

    const status =
        document.getElementById("cameraStatus");

    const startButton =
        document.getElementById("startCamera");

    try {

        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia) {

            status.textContent =
                "Camera API is not supported by this browser.";

            return;
        }


        browserStream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    width: {
                        ideal: 1280
                    },

                    height: {
                        ideal: 720
                    },

                    facingMode: "user"
                },

                audio: false

            });


        video.srcObject =
            browserStream;


        await video.play();


        status.textContent =
            "● CAMERA ONLINE";


        status.classList.add(
            "camera-online"
        );


        startButton.disabled =
            true;


        updateCameraCount();


        console.log(
            "Browser camera started"
        );

    }

    catch (error) {

        console.error(
            "Camera error:",
            error
        );


        status.textContent =
            "Camera permission denied or camera unavailable.";


        status.classList.remove(
            "camera-online"
        );

    }
}


// ============================================================
// STOP CAMERA
// ============================================================

function stopBrowserCamera() {

    const video =
        document.getElementById("browserCamera");

    const status =
        document.getElementById("cameraStatus");

    const startButton =
        document.getElementById("startCamera");


    if (browserStream) {

        browserStream
            .getTracks()
            .forEach(track => {

                track.stop();

            });

        browserStream =
            null;
    }


    video.srcObject =
        null;


    status.textContent =
        "Camera is stopped";


    status.classList.remove(
        "camera-online"
    );


    startButton.disabled =
        false;


    updateCameraCount();


    console.log(
        "Browser camera stopped"
    );
}


// ============================================================
// CAMERA COUNT
// ============================================================

function updateCameraCount(
    serverCameraCount = null
) {

    const countElement =
        document.getElementById(
            "cameraCount"
        );


    if (serverCameraCount !== null) {

        const browserCamera =
            browserStream ? 1 : 0;


        countElement.textContent =
            serverCameraCount +
            browserCamera;

        return;
    }


    fetch("/api/cameras")
        .then(response => response.json())
        .then(data => {

            const serverCount =
                Array.isArray(data.cameras)
                    ? data.cameras.length
                    : 0;


            const browserCamera =
                browserStream ? 1 : 0;


            countElement.textContent =
                serverCount +
                browserCamera;

        })
        .catch(error => {

            console.error(
                "Camera count error:",
                error
            );

        });

}


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const response =
            await fetch(
                "/api/dashboard"
            );


        if (!response.ok) {

            throw new Error(
                `Dashboard API returned ${response.status}`
            );

        }


        const data =
            await response.json();


        // ------------------------------------------------------
        // VIOLATION COUNT
        // ------------------------------------------------------

        document.getElementById(
            "violationCount"
        ).textContent =
            data.violation_count || 0;


        // ------------------------------------------------------
        // SERVER CAMERAS
        // ------------------------------------------------------

        const container =
            document.getElementById(
                "cameraGrid"
            );


        container.innerHTML =
            "";


        const camerasResponse =
            await fetch(
                "/api/cameras"
            );


        const camerasData =
            await camerasResponse.json();


        const serverCameras =
            Array.isArray(
                camerasData.cameras
            )
                ? camerasData.cameras
                : [];


        serverCameras.forEach(
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


        // ------------------------------------------------------
        // CAMERA COUNT
        // ------------------------------------------------------

        updateCameraCount(
            serverCameras.length
        );


        // ------------------------------------------------------
        // VIOLATIONS
        // ------------------------------------------------------

        const violations =
            document.getElementById(
                "violations"
            );


        violations.innerHTML =
            "";


        const recentViolations =
            Array.isArray(
                data.recent_violations
            )
                ? data.recent_violations
                : [];


        recentViolations.forEach(
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

    }

    catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }
}


// ============================================================
// BUTTONS
// ============================================================

document
    .getElementById("startCamera")
    .addEventListener(
        "click",
        startBrowserCamera
    );


document
    .getElementById("stopCamera")
    .addEventListener(
        "click",
        stopBrowserCamera
    );


// ============================================================
// START
// ============================================================

loadDashboard();


setInterval(
    loadDashboard,
    5000
);


// ============================================================
// CLEANUP
// ============================================================

window.addEventListener(
    "beforeunload",
    stopBrowserCamera
);