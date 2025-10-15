const form = document.getElementById("inviteForm");
form.addEventListener("submit", start);

const loader = document.getElementById("loader");

function displayLoading() {
  loader.hidden = false;
}

function hideLoading() {
  loader.hidden = true;
}

async function start(ev) {
  ev.preventDefault();

  console.log("start form");

  // Show in progress message
  const inProgressMsg = document.getElementById("inProgressMsg");
  inProgressMsg.hidden = false;

  const form = new FormData(ev.target);;

  const {
    fullname,
    address,
    email,
    dob,
    letterselection: lettertype,
    og,
    talk: speaker,
    passport_no
  } = Object.fromEntries(form);

  let data;

  displayLoading();

  if (lettertype == "none") {
    data = {
      "fullname": fullname,
      "address": address,
      "email": email,
      "dob": dob,
      "passport_no": passport_no
    }
  } else if (lettertype == "og") {
    data = {
      "fullname": fullname,
      "address": address,
      "email": email,
      "dob": dob,
      "passport_no": passport_no,
      "letteropt": {
        "key": "og",
        "value": og
      }
    };
  } else if (lettertype == "speaker") {
    data = {
      "fullname": fullname,
      "address": address,
      "email": email,
      "dob": dob,
      "passport_no": passport_no,
      "letteropt": {
        "key": "speaker",
        "value": speaker
      }
    };
  }

  displayLoading();

  const formElem = document.getElementById("inviteForm");
  formElem.hidden = true;

  await fetch('https://djc-invitation-letter-api-noahalorwu.vercel.app/invitation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  }).then(res => res.json()).then(data => {
    hideLoading();
    console.log(data);
    inProgressMsg.hidden = true;
    document.getElementById("readyMsg").hidden = false;
  });
}

// Update fields shown dependent upon attendee type
document.addEventListener("DOMContentLoaded", function() {
  document.getElementById("letterselection").addEventListener("change", function() {
    let selected = this.value;

    const ogElem = document.getElementById("og");
    const speakerElem = document.getElementById("speaker");

    if (selected == "none") {
      ogElem.hidden = true;
      speakerElem.hidden = true;
    }
    else if (selected == "og") {
      ogElem.hidden = false;
      speakerElem.hidden = true;
    }
    else if (selected == "speaker") {
      ogElem.hidden = true;
      speakerElem.hidden = false;
    }
  });
});
