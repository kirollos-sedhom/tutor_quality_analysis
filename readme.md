## if you want to stop the project
Here is the exact protocol to kill the process, sever the automation, and regain manual control:

1. Kill the Active Process
Right now, the script is running in your computer's memory. We need to terminate it.

Press Ctrl + Shift + Esc to open the Windows Task Manager.

Click on the "Details" tab on the left sidebar (it looks like a bulleted list icon).

Scroll down to the 'P' section and look for pythonw.exe. (The 'w' indicates the windowless Python executable running your script).

Right-click pythonw.exe and select "End task".

The script is now dead. It is no longer monitoring your folders.

2. Sever the Automation (Stop the Auto-Start)
If you restart your computer right now, the script will come back to life because the shortcut is still in the startup sequence.

Press the Windows Key + R.

Type shell:startup and hit Enter.

Delete the shortcut you placed in that folder.

Your computer will no longer launch this script automatically.

3. Edit or Destroy the Code
Now that the system is idle, you dictate what happens to the files.

To destroy it: Simply delete your quality_reports project folder.

To edit it: You do not need to rename the file back to .py to edit it. You can right-click the pipeline.pyw file, select "Open with," and choose your code editor (like VS Code or Notepad) to change the logic.