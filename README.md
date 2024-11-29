# **Demonstration**

https://github.com/user-attachments/assets/de56573c-c2df-4d00-afdb-fd00ed8c6b6a

# **A Simple Video Streaming Platform**

This project is a lightweight video streaming platform built with **Flask**. It allows users to upload and stream videos efficiently using **HTTP Live Streaming (HLS)** and HTTP range requests for smooth playback.

---

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

### **1. Clone the Repository**

```bash
git clone https://github.com/tushar1977/Video-Streaming-Plateform
cd Video-Streaming-Plateform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=myserver
python3 run.py
```
