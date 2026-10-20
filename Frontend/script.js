const API_URL = window.location.origin.includes("5000") ? window.location.origin : "http://127.0.0.1:5000";

/* =======================================================
LOGIN
======================================================= */

async function loginUser(email, password, department=null) {

    try {

        const res = await fetch(`${API_URL}/login`, {

            method: "POST",

            credentials: "include",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                email: email,
                password: password,
                department: department
            })

        });

        const data = await res.json();

        if(data.status === "success"){

            if(data.role === "authority"){

                window.location.href = "authority.html";

            }

            else if(data.role === "citizen"){

                window.location.href = "citizen.html";

            }

        }

        else{

            alert(data.error || "Login failed");

        }

    }

    catch(err){

        alert("Server error. Make sure backend is running.");

    }

}



/* =======================================================
SIGNUP
======================================================= */

async function signupUser(name, email, password, phone = "") {

    try {

        const res = await fetch(`${API_URL}/signup`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name,
                email,
                password,
                phone_number: phone
            })

        });

        const data = await res.json();

        if (data.status === "signup_success") {

            alert("Account created successfully");

            window.location.href = "citizen_login.html";

        }

        else {

            alert(data.error);

        }

    }

    catch (err) {

        alert("Server error");

    }

}



/* =======================================================
LOGOUT
======================================================= */

async function logoutUser() {

    await fetch(`${API_URL}/logout`, {

        credentials: "include"

    });

    window.location.href = "index.html";

}



/* =======================================================
GET CURRENT USER INFO
======================================================= */

async function loadUserNavbar(){

    try{

        const res = await fetch(`${API_URL}/user_info`,{
            credentials:"include"
        });

        if(res.status !== 200) return;

        const user = await res.json();

        const navUser = document.getElementById("navUser");

        if(navUser){

            navUser.innerHTML = `
            <div class="dropdown">

            ${user.name} ▼

            <div class="dropdown-content">

            <a href="profile.html">My Profile</a>

            <a href="#" onclick="logoutUser()">Logout</a>

            </div>

            </div>
            `;
        }

    }

    catch(err){

        console.log("User not logged in");

    }

}



/* =======================================================
UPDATE PROFILE
======================================================= */

async function updateProfile(){

    const name = document.getElementById("name").value;

    const phone = document.getElementById("phone").value;

    const image = document.getElementById("profile_picture").files[0];

    const formData = new FormData();

    formData.append("name",name);
    formData.append("phone",phone);

    if(image){
        formData.append("profile_picture",image);
    }

    const res = await fetch(`${API_URL}/update_profile`,{

        method:"POST",

        credentials:"include",

        body:formData

    });

    const data = await res.json();

    if(data.status==="profile_updated"){

        alert("Profile updated successfully");

    }

}



/* =======================================================
SUBMIT COMPLAINT
======================================================= */

async function submitComplaint() {

    const text = document.getElementById("desc").value;

    const severity = document.getElementById("severity").value;

    const location = document.getElementById("location").value;

    const image = document.getElementById("image").files[0];

    const formData = new FormData();

    formData.append("complaint_text", text);
    formData.append("severity", severity);
    formData.append("location", location);

    if (image) {

        formData.append("image", image);

    }

    try {

        const res = await fetch(`${API_URL}/submit_complaint`, {

            method: "POST",

            credentials: "include",

            body: formData

        });

        const data = await res.json();

        if (data.status === "success") {


            document.getElementById("complaintForm").reset();

            fetchComplaints("citizen");

        }

        else {

            alert(data.error);

        }

    }

    catch (err) {

        alert("Server error while submitting complaint");

    }

}



/* =======================================================
FETCH COMPLAINTS
======================================================= */

async function fetchComplaints(role) {

    try {

        const res = await fetch(`${API_URL}/complaints`, {

            credentials: "include"

        });

        if (res.status === 401) {

            alert("Session expired. Please login again");

            window.location.href = "index.html";

            return;

        }

        const data = await res.json();

        if (!data.data) return;

        if (role === "citizen") {

            renderCitizenFeed(data.data);

        }

        else if (role === "authority") {

            renderAuthorityTable(data.data);

        }

    }

    catch (err) {

        console.log("Error fetching complaints");

    }

}



/* =======================================================
CITIZEN FEED
======================================================= */

function renderCitizenFeed(complaints) {

    const feed = document.getElementById("complaintFeed");

    if (!feed) return;

    feed.innerHTML = "";

    complaints.forEach(c => {

        const div = document.createElement("div");

        div.className = "complaint-item card";
        div.style.marginBottom = "20px";

        let commentsHtml = "";
        if (c.comments && c.comments.length > 0) {
            commentsHtml = `<div class="comments-section" style="margin-top: 10px; background: #f8fafc; padding: 10px; border-radius: 6px;">
                <strong>Comments:</strong>
                ${c.comments.map(cm => `<div style="font-size: 0.9rem; margin-top: 4px;"><b>${cm.name}:</b> ${cm.comment_text}</div>`).join('')}
            </div>`;
        }

        const imageHtml = c.image_path ? `<div style="margin: 10px 0;"><img src="${API_URL}/uploads/${c.image_path}" style="max-width: 100%; max-height: 250px; border-radius: 8px;"></div>` : '';

        const summaryHtml = c.official_summary ? `<div style="font-size: 0.85rem; background: #eff6ff; color: #1e40af; padding: 8px; border-radius: 6px; margin: 8px 0;"><strong>🤖 AI Official Summary:</strong> ${c.official_summary}</div>` : '';

        div.innerHTML = `

        <div>

        <div style="display: flex; justify-content: space-between; align-items: center;">
            <b>${c.name}</b> 
            <span style="font-size: 0.8rem; background: #e2e8f0; padding: 2px 8px; border-radius: 12px; text-transform: uppercase;">${c.category || 'General'}</span>
        </div>
        <small style="color: #64748b;">📍 ${c.location} | Severity: ${c.severity || 'N/A'}</small>
        
        <p style="margin: 10px 0 5px 0;">${c.complaint_text}</p>

        ${summaryHtml}

        ${imageHtml}

        <div style="display: flex; gap: 15px; align-items: center; margin-top: 10px;">
            <div class="status" style="font-weight: 600; text-transform: capitalize;">Status: <span style="color: ${c.status==='closed'?'green':(c.status==='in_progress'?'orange':'red')}">${c.status}</span></div>

            <button onclick="likeComplaint(${c.id})" class="support-btn" style="cursor: pointer; background: #e0e7ff; color: #3730a3; border: none; padding: 5px 12px; border-radius: 6px;">
                ❤️ ${c.support_count} Support
            </button>
        </div>

        <div style="margin-top: 12px; display: flex; gap: 8px;">
            <input id="comment-${c.id}" placeholder="Write a comment..." style="flex: 1; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;">
            <button onclick="addComment(${c.id})" class="comment-btn" style="background: #2563eb; color: white; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer;">
            Comment
            </button>
        </div>

        ${commentsHtml}

        </div>

  `;
        feed.appendChild(div);

    });

}

async function addComment(id){

const input = document.getElementById(`comment-${id}`);
const text = input.value;

if(!text){
alert("Write a comment");
return;
}

await fetch(`${API_URL}/complaints/${id}/comment`,{

method:"POST",

credentials:"include",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
comment:text
})

});

input.value="";

/* refresh complaints so comments appear */

fetchComplaints("citizen");

}

/* =======================================================
AUTHORITY TABLE
======================================================= */

function renderAuthorityTable(complaints) {

    const table = document.getElementById("adminTableBody");

    if (!table) return;

    table.innerHTML = "";

    complaints.forEach(c => {

        const row = `

        <tr>

        <td>${c.id}</td>

        <td>${c.category}</td>

        <td>${c.severity}</td>

        <td>${c.location}</td>

        <td>${c.priority}</td>

        <td>${c.status}</td>

        <td>${c.support_count}</td>

        <td>

        <select onchange="updateStatus(${c.id}, this.value)">

        <option value="open" ${c.status === "open" ? "selected":""}>Open</option>

        <option value="in_progress" ${c.status === "in_progress" ? "selected":""}>In Progress</option>

        <option value="closed" ${c.status === "closed" ? "selected":""}>Closed</option>

        </select>

        </td>

        </tr>

        `;

        table.innerHTML += row;

    });

}



/* =======================================================
LIKE COMPLAINT
======================================================= */

async function likeComplaint(id){

    try {
        const res = await fetch(`${API_URL}/complaints/${id}/like`,{
            method:"POST",
            credentials:"include"
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || "Could not register support");
        }
    } catch(err) {
        alert("Network error while registering support");
    }

    fetchComplaints("citizen");

}



/* =======================================================
UPDATE STATUS
======================================================= */

async function updateStatus(id,status){

    await fetch(`${API_URL}/complaints/${id}/status`,{

        method:"PUT",

        credentials:"include",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            status:status
        })

    });

    fetchComplaints("authority");

}
