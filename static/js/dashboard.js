document.addEventListener("DOMContentLoaded", () => {
    // 1. KHỞI TẠO KHÔNG GIAN 3D THREE.JS
    const container = document.getElementById("threeContainer");
    container.style.position = "relative";
    container.style.cursor = "grab";

    container.addEventListener("mousedown", () => container.style.cursor = "grabbing");
    window.addEventListener("mouseup", () => container.style.cursor = "grab");

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x090f1d);

    const width = container.clientWidth || 360;
    const height = container.clientHeight || 350;
    const camera3D = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
    camera3D.position.set(52, 42, 52);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width > 0 ? width : 360, height > 0 ? height : 350);
    container.appendChild(renderer.domElement);

    setTimeout(() => {
        const w = container.clientWidth || 360;
        const h = container.clientHeight || 350;
        camera3D.aspect = w / h;
        camera3D.updateProjectionMatrix();
        renderer.setSize(w, h);
    }, 100);

    const controls = new THREE.OrbitControls(camera3D, renderer.domElement);
    controls.target.set(15, 12, 15);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.enableZoom = true;
    controls.enablePan = true;
    controls.autoRotate = false;
    controls.update();

    // Thanh góc nhìn nhanh 3D
    const viewBar = document.createElement("div");
    viewBar.style.cssText = "position:absolute; top:8px; left:8px; right:8px; display:flex; gap:5px; flex-wrap:wrap; z-index:10; pointer-events:auto;";
    const views = [
        { label: "Góc 3D", pos: [52, 42, 52], target: [15, 12, 15] },
        { label: "Từ Trên (Oxy)", pos: [15, 68, 15.01], target: [15, 0, 15] },
        { label: "Vách Ox", pos: [65, 15, 15], target: [0, 15, 15] },
        { label: "Vách Oy", pos: [15, 15, 65], target: [15, 15, 0] }
    ];

    views.forEach(v => {
        const b = document.createElement("button");
        b.innerText = v.label;
        b.style.cssText = "background:rgba(30,41,59,0.85); color:#38bdf8; border:1px solid #334155; border-radius:4px; padding:3px 7px; font-size:11px; font-weight:600; cursor:pointer;";
        b.onclick = () => {
            controls.autoRotate = false;
            camera3D.position.set(...v.pos);
            controls.target.set(...v.target);
            controls.update();
        };
        viewBar.appendChild(b);
    });

    const btnAutoRotate = document.createElement("button");
    btnAutoRotate.innerText = "Tự Xoay";
    btnAutoRotate.style.cssText = "background:rgba(30,41,59,0.85); color:#cbd5e1; border:1px solid #334155; border-radius:4px; padding:3px 7px; font-size:11px; font-weight:600; cursor:pointer;";
    btnAutoRotate.onclick = () => {
        controls.autoRotate = !controls.autoRotate;
        btnAutoRotate.style.background = controls.autoRotate ? "#0284c7" : "rgba(30,41,59,0.85)";
        btnAutoRotate.style.color = "#fff";
    };
    viewBar.appendChild(btnAutoRotate);
    container.appendChild(viewBar);

    // Khung hộp 30x30x30
    const boxGeo = new THREE.BoxGeometry(30, 30, 30);
    const edges = new THREE.EdgesGeometry(boxGeo);
    const boxLines = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x1e3a5f, linewidth: 1 }));
    boxLines.position.set(15, 15, 15);
    scene.add(boxLines);

    const gridBottom = new THREE.GridHelper(30, 10, 0x0284c7, 0x1e293b);
    gridBottom.position.set(15, 0, 15);
    scene.add(gridBottom);

    const gridLeft = new THREE.GridHelper(30, 10, 0x334155, 0x1e293b);
    gridLeft.rotation.z = Math.PI / 2;
    gridLeft.position.set(0, 15, 15);
    scene.add(gridLeft);

    const gridRight = new THREE.GridHelper(30, 10, 0x334155, 0x1e293b);
    gridRight.rotation.x = Math.PI / 2;
    gridRight.position.set(15, 15, 0);
    scene.add(gridRight);

    function createAxisLabel(text, colorHex) {
        const canvas = document.createElement("canvas");
        canvas.width = 160;
        canvas.height = 80;
        const ctx2d = canvas.getContext("2d");
        ctx2d.font = "bold 36px sans-serif";
        ctx2d.fillStyle = colorHex;
        ctx2d.textAlign = "center";
        ctx2d.textBaseline = "middle";
        ctx2d.fillText(text, 80, 40);

        const texture = new THREE.CanvasTexture(canvas);
        const spriteMat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.set(8, 4, 1);
        return sprite;
    }

    function createAxisLine(start, end, colorHex) {
        const pts = [new THREE.Vector3(...start), new THREE.Vector3(...end)];
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const mat = new THREE.LineBasicMaterial({ color: colorHex, linewidth: 3 });
        return new THREE.Line(geo, mat);
    }

    scene.add(createAxisLine([0, 0, 0], [0, 0, 32], 0x38bdf8));
    const lblOx = createAxisLabel("Ox", "#38bdf8");
    lblOx.position.set(0, 1.5, 34);
    scene.add(lblOx);

    scene.add(createAxisLine([0, 0, 0], [32, 0, 0], 0x4ade80));
    const lblOy = createAxisLabel("Oy", "#4ade80");
    lblOy.position.set(34, 1.5, 0);
    scene.add(lblOy);

    scene.add(createAxisLine([0, 0, 0], [0, 32, 0], 0xf87171));
    const lblOz = createAxisLabel("Oz", "#f87171");
    lblOz.position.set(0, 34, 0);
    scene.add(lblOz);

    const lblO = createAxisLabel("O", "#f59e0b");
    lblO.position.set(-2, 2, -2);
    scene.add(lblO);

    const sphereGeo = new THREE.SphereGeometry(1.5, 32, 32);
    const sphereMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const targetSphere = new THREE.Mesh(sphereGeo, sphereMat);
    targetSphere.position.set(15, 0, 15);
    scene.add(targetSphere);

    const dropGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(15, 0, 15), new THREE.Vector3(15, 0, 15)]);
    const dropLine = new THREE.Line(dropGeo, new THREE.LineDashedMaterial({ color: 0xf87171, dashSize: 1, gapSize: 1 }));
    scene.add(dropLine);

    function update3DPosition(x, y, z) {
        targetSphere.position.set(y, z, x);
        const dropPts = [new THREE.Vector3(y, z, x), new THREE.Vector3(y, 0, x)];
        dropLine.geometry.setFromPoints(dropPts);
        dropLine.computeLineDistances();
    }

    let lastLogTime = "";
    function addHistoryRow(timeStr, coords, statusText) {
        if (!timeStr || timeStr === lastLogTime) return;
        lastLogTime = timeStr;
        const tbody = document.getElementById("historyTableBody");
        if (!tbody) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${timeStr}</td>
            <td style="color:#38bdf8;font-weight:bold;">${coords.x}</td>
            <td style="color:#4ade80;font-weight:bold;">${coords.y}</td>
            <td style="color:#f87171;font-weight:bold;">${coords.z}</td>
            <td>${statusText}</td>
        `;
        tbody.insertBefore(tr, tbody.firstChild);
        while (tbody.children.length > 15) tbody.removeChild(tbody.lastChild);
    }

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera3D);
    }
    animate();

    window.addEventListener("resize", () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera3D.aspect = w / h;
        camera3D.updateProjectionMatrix();
        renderer.setSize(w, h);
    });

    // 2. TÍNH NĂNG ZOOM CHO KHUNG CAMERA
    let currentZoom = 1.0;
    const camInner = document.getElementById("camInner");
    const btnZoomIn = document.getElementById("btnZoomIn");
    const btnZoomOut = document.getElementById("btnZoomOut");
    const btnZoomReset = document.getElementById("btnZoomReset");

    if (btnZoomIn && btnZoomOut && btnZoomReset && camInner) {
        btnZoomIn.onclick = () => {
            currentZoom = Math.min(3.0, currentZoom + 0.25);
            camInner.style.transform = `scale(${currentZoom})`;
            btnZoomReset.innerText = Math.round(currentZoom * 100) + "%";
        };

        btnZoomOut.onclick = () => {
            currentZoom = Math.max(1.0, currentZoom - 0.25);
            camInner.style.transform = `scale(${currentZoom})`;
            btnZoomReset.innerText = Math.round(currentZoom * 100) + "%";
        };

        btnZoomReset.onclick = () => {
            currentZoom = 1.0;
            camInner.style.transform = `scale(1.0)`;
            btnZoomReset.innerText = "100%";
        };
    }

    // 3. TẢI ẢNH LÊN DỰ PHÒNG & ĐO TỌA ĐỘ
    const btnUploadImage = document.getElementById("btnUploadImage");
    const imageFileInput = document.getElementById("imageFileInput");
    const videoFeed = document.getElementById("videoFeed");

    if (btnUploadImage && imageFileInput) {
        btnUploadImage.addEventListener("click", () => imageFileInput.click());
        imageFileInput.addEventListener("change", () => {
            if (!imageFileInput.files || imageFileInput.files.length === 0) return;
            const file = imageFileInput.files[0];
            const formData = new FormData();
            formData.append("image", file);
            btnUploadImage.innerText = "Đang xử lý ảnh...";

            fetch("/api/upload_image", { method: "POST", body: formData })
            .then(r => r.json())
            .then(res => {
                btnUploadImage.innerText = "Tải Ảnh Lên (Dự phòng)";
                if (res.success) {
                    videoFeed.src = res.image_b64;
                    if (res.coords) {
                        document.getElementById("detectStateText").innerText = "Đã phát hiện qua ảnh tải lên";
                        document.getElementById("detectStateText").style.color = "#4ade80";
                        document.getElementById("valX").innerText = res.coords.x;
                        document.getElementById("valY").innerText = res.coords.y;
                        document.getElementById("valZ").innerText = res.coords.z;
                        update3DPosition(res.coords.x, res.coords.y, res.coords.z);
                        addHistoryRow(new Date().toLocaleTimeString("vi-VN", { hour12: false }), res.coords, "Ảnh tải lên");
                    } else {
                        document.getElementById("detectStateText").innerText = res.message;
                        document.getElementById("detectStateText").style.color = "#ef4444";
                    }
                } else alert("Lỗi tải ảnh: " + res.message);
            }).catch(() => {
                btnUploadImage.innerText = "Tải Ảnh Lên (Dự phòng)";
                alert("Lỗi kết nối server!");
            });
        });
    }

    // 4. ĐỔI CAMERA
    const btnSwitchCam = document.getElementById("btnSwitchCam");
    const cameraSelect = document.getElementById("cameraSelect");
    if (btnSwitchCam && cameraSelect) {
        btnSwitchCam.addEventListener("click", () => {
            const idx = cameraSelect.value;
            fetch("/api/camera/switch", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ index: idx })
            }).then(r => r.json()).then(res => {
                if (res.success) {
                    alert("Đã chuyển sang Camera " + idx);
                    videoFeed.src = "/video_feed?t=" + new Date().getTime();
                } else alert("Lỗi mở camera: " + res.message);
            });
        });
    }

    // 5. HIỆU CHUẨN 5 ĐIỂM (Tự động đồng bộ kích thước canvas để hiện rõ chấm đỏ)
    let isCalibrating = false;
    let calibPoints = [];
    const btnStartCalib = document.getElementById("btnStartCalib");
    const overlay = document.getElementById("overlayCanvas");
    const ctx = overlay.getContext("2d");

    function resizeCanvas() {
        if (videoFeed.clientWidth > 0 && videoFeed.clientHeight > 0) {
            overlay.width = videoFeed.clientWidth;
            overlay.height = videoFeed.clientHeight;
        } else {
            overlay.width = videoFeed.offsetWidth || 400;
            overlay.height = videoFeed.offsetHeight || 300;
        }
    }
    
    window.addEventListener("resize", resizeCanvas);

    fetch("/api/calibrate/status")
        .then(r => r.json())
        .then(status => {
            if (status.calibrated) {
                document.getElementById("calibStateText").innerText = "Đã hiệu chuẩn";
                document.getElementById("calibStateText").style.color = "#4ade80";
            }
        }).catch(() => {});

    btnStartCalib.addEventListener("click", () => {
        isCalibrating = true;
        calibPoints = [];
        resizeCanvas();
        ctx.clearRect(0, 0, overlay.width, overlay.height);
        alert("Bắt đầu chọn 5 điểm:\n1. Gốc O(0,0,0)\n2. Điểm X(30,0,0) - Vách trái\n3. Điểm Chéo(30,30,0)\n4. Điểm Y(0,30,0) - Vách phải\n5. Đỉnh Z(0,0,30) - Trục đứng");
    });

    overlay.addEventListener("click", (e) => {
        if (!isCalibrating) return;
        resizeCanvas();
        const rect = overlay.getBoundingClientRect();
        
        const renderX = e.clientX - rect.left;
        const renderY = e.clientY - rect.top;

        const clickX = renderX / currentZoom;
        const clickY = renderY / currentZoom;

        const scaleX = (videoFeed.naturalWidth || overlay.width) / overlay.width;
        const scaleY = (videoFeed.naturalHeight || overlay.height) / overlay.height;

        calibPoints.push([clickX * scaleX, clickY * scaleY]);

        // Vẽ chấm đỏ bán kính 3.5 nhỏ gọn và nhãn P rõ ràng
        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.arc(renderX, renderY, 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();

        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 12px sans-serif";
        ctx.fillText("P" + calibPoints.length, renderX + 8, renderY - 4);

        if (calibPoints.length === 5) {
            isCalibrating = false;
            fetch("/api/calibrate/corners", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ corners: calibPoints })
            }).then(r => r.json()).then(res => {
                alert(res.message);
                ctx.clearRect(0, 0, overlay.width, overlay.height);
                document.getElementById("calibStateText").innerText = "Đã hiệu chuẩn";
                document.getElementById("calibStateText").style.color = "#4ade80";
            });
        }
    });

    document.getElementById("btnSaveBg").addEventListener("click", () => {
        fetch("/api/background/capture", { method: "POST" })
            .then(r => r.json()).then(res => alert(res.message));
    });

    let running = true;
    document.getElementById("btnToggleProcess").addEventListener("click", () => {
        running = !running;
        fetch("/api/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ running })
        }).then(r => r.json()).then(res => {
            document.getElementById("btnToggleProcess").innerText = res.running ? "Dừng Xử Lý" : "Tiếp Tục Xử Lý";
        });
    });

    setInterval(() => {
        fetch("/api/coordinates")
            .then(r => r.json())
            .then(data => {
                if (data.detected && data.coords) {
                    document.getElementById("detectStateText").innerText = "Đã phát hiện vật thể";
                    document.getElementById("detectStateText").style.color = "#4ade80";
                    document.getElementById("valX").innerText = data.coords.x;
                    document.getElementById("valY").innerText = data.coords.y;
                    document.getElementById("valZ").innerText = data.coords.z;
                    update3DPosition(data.coords.x, data.coords.y, data.coords.z);
                    addHistoryRow(data.timestamp, data.coords, "Đã phát hiện");
                } else {
                    document.getElementById("detectStateText").innerText = data.message || "Chưa phát hiện vật thể";
                    document.getElementById("detectStateText").style.color = "#ef4444";
                }
            }).catch(() => {});
    }, 150);
});