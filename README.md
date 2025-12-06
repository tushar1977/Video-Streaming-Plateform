# **Demonstration**

https://drive.google.com/file/d/1CCmGtLZsCzBPgmsFzEuwgr2yDsJvWd9v/view?usp=sharing

# **A Simple Video Streaming Platform**

This project is a lightweight video streaming platform built with **Flask**. It allows users to upload and stream videos efficiently using **HTTP Live Streaming (HLS)** and HTTP range requests for smooth playback.

---

## **Architecture**

<img width="1538" height="1745" alt="trans" src="https://github.com/user-attachments/assets/81b4bee5-962b-4ef8-b0b2-22202d5dcb40" />

## **Features**

- **Efficient Video Streaming**

  - Implements **HLS** to parse and serve video in small segments, ensuring adaptive streaming.
  - Utilizes **HTTP range requests** to deliver video chunks dynamically for seamless playback.

- **Video Upload**

  - Allows users to upload video files directly from the platform.

- **Responsive Playback**
  - Ensures smooth streaming on various devices and networks by breaking videos into manageable segments.

---

## **Getting Started**

Follow these steps to set up and run the platform locally. _(Soon to be deployed on a live server!)_
### **1. First generate SSL certificates
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### **2. Clone the Repository**

```bash
git clone https://github.com/tushar1977/Video-Streaming-Plateform
cd Video-Streaming-Plateform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py && python3 run_upload.py
```
