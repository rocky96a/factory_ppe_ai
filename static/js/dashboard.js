let browserStream = null;
let browserCameraRunning = false;
let frameTimer = null;
let processingFrame = false;

const FRAME_INTERVAL = 500;


// ============================================================
// BROWSER CAMERA
// ============================================================

async function startBrowserCamera() {

    const video = document.getElementById("browserCamera");
    const status = document.getElementById("cameraStatus");
    const startButton = document.getElementById("startCamera");

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
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: "user"
                },

                audio: false
            });

        video.srcObject = browserStream;

        await video.play();

        browserCameraRunning = true;

        status.textContent =
            "● CAMERA ONLINE — AI STARTING";

        status.classList.add("camera-online");

        startButton.disabled = true;

        updateCameraCount();

        startBrowserAI();

        console.log(
            "Browser camera started"
        );

    } catch (error) {

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


    browserCameraRunning = false;


    if (frameTimer) {

        clearTimeout(
            frameTimer
        );

        frameTimer = null;
    }


    processingFrame = false;


    if (browserStream) {

        browserStream
            .getTracks()
            .forEach(track => {

                track.stop();

            });

        browserStream = null;
    }


    video.srcObject = null;

    clearBrowserOverlay();


    status.textContent =
        "Camera is stopped";

    status.classList.remove(
        "camera-online"
    );


    startButton.disabled = false;


    updateCameraCount();


    console.log(
        "Browser camera stopped"
    );
}


// ============================================================
// START AI LOOP
// ============================================================

function startBrowserAI() {

    if (!browserCameraRunning) {
        return;
    }

    sendBrowserFrame();
}


// ============================================================
// CAPTURE + SEND FRAME
// ============================================================

async function sendBrowserFrame() {

    if (!browserCameraRunning) {
        return;
    }

    if (processingFrame) {

        scheduleNextFrame();

        return;
    }


    const video =
        document.getElementById(
            "browserCamera"
        );


    if (
        !video.videoWidth ||
        !video.videoHeight
    ) {

        scheduleNextFrame();

        return;
    }


    processingFrame = true;


    try {

        const canvas =
            document.createElement(
                "canvas"
            );


        const maxWidth = 960;

        let width =
            video.videoWidth;

        let height =
            video.videoHeight;


        if (width > maxWidth) {

            const scale =
                maxWidth / width;

            width =
                Math.round(
                    width * scale
                );

            height =
                Math.round(
                    height * scale
                );
        }


        canvas.width = width;
        canvas.height = height;


        const context =
            canvas.getContext(
                "2d"
            );


        context.drawImage(
            video,
            0,
            0,
            width,
            height
        );


        const image =
            canvas.toDataURL(
                "image/jpeg",
                0.70
            );


        const response =
            await fetch(
                "/api/browser-camera/frame",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        image: image
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `AI API returned ${response.status}`
            );
        }


        const data =
            await response.json();


        if (
            data.success &&
            data.result
        ) {

            updateBrowserAI(
                data.result
            );
        }


    } catch (error) {

        console.error(
            "Browser AI error:",
            error
        );

        const status =
            document.getElementById(
                "cameraStatus"
            );

        status.textContent =
            "● CAMERA ONLINE — AI CONNECTION ERROR";

    } finally {

        processingFrame = false;

        scheduleNextFrame();
    }
}


// ============================================================
// SCHEDULE NEXT FRAME
// ============================================================

function scheduleNextFrame() {

    if (!browserCameraRunning) {
        return;
    }

    frameTimer =
        setTimeout(
            sendBrowserFrame,
            FRAME_INTERVAL
        );
}


// ============================================================
// UPDATE AI STATUS
// ============================================================

function updateBrowserAI(result) {

    const status =
        document.getElementById(
            "cameraStatus"
        );


    const people =
        result.person_count || 0;

    const noHelmet =
        result.no_helmet_count || 0;

    const helmets =
        result.helmet_count || 0;

    const unknown =
        result.unknown_count || 0;


    if (noHelmet > 0) {

        status.textContent =
            `● AI ACTIVE — ${people} PEOPLE — ${noHelmet} NO HELMET`;

    } else {

        status.textContent =
            `● AI ACTIVE — ${people} PEOPLE — ${helmets} HELMET`;

        if (unknown > 0) {

            status.textContent +=
                ` — ${unknown} UNKNOWN`;
        }
    }


    status.classList.add(
        "camera-online"
    );


    updateBrowserPeople(
        result.people || []
    );

    drawBrowserOverlay(
        result.people || []
    );
}


// ============================================================
// DISPLAY DETECTED PEOPLE
// ============================================================

function updateBrowserPeople(people) {

    let panel =
        document.getElementById(
            "browserPeople"
        );


    if (!panel) {

        const cameraSection =
            document.querySelector(
                ".browser-camera-section"
            );


        if (!cameraSection) {
            return;
        }


        panel =
            document.createElement(
                "div"
            );


        panel.id =
            "browserPeople";

        panel.className =
            "browser-people-panel";


        cameraSection.appendChild(
            panel
        );
    }


    if (!people.length) {

        panel.innerHTML =
            "<strong>No people detected</strong>";

        return;
    }


    let html =
        `<strong>Detected People: ${people.length}</strong>`;


    people.forEach(
        (person, index) => {

            const status =
                person.helmet_status ||
                "UNKNOWN";


            const confidence =
                (
                    (person.helmet_confidence || 0)
                    * 100
                ).toFixed(1);


            html += `
                <div class="browser-person">
                    <span>
                        Person ${index + 1}
                    </span>

                    <span>
                        ID:
                        ${person.track_id ?? "-"}
                    </span>

                    <span>
                        ${status}
                    </span>

                    <span>
                        ${confidence}%
                    </span>
                </div>
            `;
        }
    );


    panel.innerHTML =
        html;
}


// ============================================================
// DRAW AI BOUNDING BOXES
// ============================================================

function drawBrowserOverlay(people) {

    const video =
        document.getElementById("browserCamera");

    const canvas =
        document.getElementById("browserOverlay");

    if (!video || !canvas) {
        return;
    }

    if (!video.videoWidth || !video.videoHeight) {
        return;
    }

    const context =
        canvas.getContext("2d");

    canvas.width =
        video.videoWidth;

    canvas.height =
        video.videoHeight;

    context.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    people.forEach((person, index) => {

        const bbox =
            person.bbox;

        if (!bbox || bbox.length !== 4) {
            return;
        }

        const x1 = Number(bbox[0]);
        const y1 = Number(bbox[1]);
        const x2 = Number(bbox[2]);
        const y2 = Number(bbox[3]);

        const width =
            x2 - x1;

        const height =
            y2 - y1;

        if (width <= 0 || height <= 0) {
            return;
        }


        const helmetStatus =
            person.helmet_status ||
            "UNKNOWN";


        // ----------------------------------------------------
        // BOX COLOR
        // ----------------------------------------------------

        if (helmetStatus === "NO_HELMET") {

            context.strokeStyle =
                "#ef4444";

        } else if (helmetStatus === "HELMET") {

            context.strokeStyle =
                "#22c55e";

        } else {

            context.strokeStyle =
                "#f59e0b";
        }


        context.lineWidth = 4;

        context.strokeRect(
            x1,
            y1,
            width,
            height
        );


        // ----------------------------------------------------
        // LABEL
        // ----------------------------------------------------

        const trackId =
            person.track_id ?? "-";

        const confidence =
            (
                Number(
                    person.helmet_confidence || 0
                ) * 100
            ).toFixed(0);


        let label =
            `Person ${index + 1} | ID ${trackId} | ${helmetStatus}`;


        if (helmetStatus !== "UNKNOWN") {

            label +=
                ` ${confidence}%`;
        }


        context.font =
            "bold 16px Arial";


        const textWidth =
            context.measureText(
                label
            ).width;


        const labelWidth =
            textWidth + 16;

        const labelHeight =
            28;


        const labelX =
            Math.max(
                0,
                x1
            );

        const labelY =
            Math.max(
                labelHeight,
                y1
            );


        context.fillStyle =
            "rgba(0, 0, 0, 0.80)";


        context.fillRect(
            labelX,
            labelY - labelHeight,
            labelWidth,
            labelHeight
        );


        context.fillStyle =
            "#ffffff";


        context.fillText(
            label,
            labelX + 8,
            labelY - 8
        );

    });
}


// ============================================================
// CLEAR AI OVERLAY
// ============================================================

function clearBrowserOverlay() {

    const canvas =
        document.getElementById(
            "browserOverlay"
        );

    if (!canvas) {
        return;
    }

    const context =
        canvas.getContext("2d");

    context.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
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


    fetch(
        "/api/cameras"
    )
        .then(
            response =>
                response.json()
        )
        .then(
            data => {

                const serverCount =
                    Array.isArray(
                        data.cameras
                    )
                        ? data.cameras.length
                        : 0;


                const browserCamera =
                    browserStream ? 1 : 0;


                countElement.textContent =
                    serverCount +
                    browserCamera;
            }
        )
        .catch(
            error => {

                console.error(
                    "Camera count error:",
                    error
                );

            }
        );
}


// ============================================================
// DASHBOARD
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


        document.getElementById(
            "violationCount"
        ).textContent =
            data.violation_count || 0;


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


        updateCameraCount(
            serverCameras.length
        );


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
                        ${(violation.confidence * 100).toFixed(1)}%

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


// ============================================================
// BUTTONS
// ============================================================

document
    .getElementById(
        "startCamera"
    )
    .addEventListener(
        "click",
        startBrowserCamera
    );


document
    .getElementById(
        "stopCamera"
    )
    .addEventListener(
        "click",
        stopBrowserCamera
    );


// ============================================================
// INITIAL LOAD
// ============================================================

loadDashboard();

setInterval(
    loadDashboard,
    5000
);


window.addEventListener(
    "beforeunload",
    stopBrowserCamera
);
