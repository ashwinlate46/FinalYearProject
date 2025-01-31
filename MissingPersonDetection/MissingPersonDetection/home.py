import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image
from PIL import ImageTk
import threading
import shutil
from facerec import *
from register import *
from face_detection import *
from dbHandler import *
import time
import csv
import numpy as np
import ntpath
import os

active_page = 0
thread_event = None
left_frame = None
right_frame = None
heading = None
webcam = None
img_label = None
img_read = None
img_list = []
slide_caption = None
slide_control_panel = None
current_slide = -1

root = tk.Tk()
root.geometry("1000x900+200+100")

pages = []
for i in range(5):
    pages.append(tk.Frame(root, bg="#ADD8E6"))
    pages[i].pack(side="top", fill="both", expand=True)
    pages[i].place(x=0, y=0, relwidth=1, relheight=1)


def goBack():
    global active_page, thread_event, webcam

    if (active_page==4 and not thread_event.is_set()):
        thread_event.set()
        webcam.release()

    for widget in pages[active_page].winfo_children():
        widget.destroy()

    pages[0].lift()
    active_page = 0

def basicPageSetup(pageNo):
    global left_frame, right_frame, heading

    back_img = tk.PhotoImage(file= r".\img\back.png")
    back_button = tk.Button(pages[pageNo], image=back_img, bg="#ADD8E6", bd=0, highlightthickness=0,
           activebackground="#ADD8E6", command=goBack)
    back_button.image = back_img
    back_button.place(x=10, y=10)

    heading = tk.Label(pages[pageNo], fg="white", bg="#ADD8E6", font="Arial 20 bold", pady=10)
    heading.pack()

    content = tk.Frame(pages[pageNo], bg="#ADD8E6", pady=20)
    content.pack(expand="true", fill="both")

    left_frame = tk.Frame(content, bg="#ADD8E6")
    left_frame.grid(row=0, column=0, sticky="nsew")

    right_frame = tk.LabelFrame(content, text="Detected Missing People", bg="#ADD8E6", font="Arial 20 bold", bd=4,
                             foreground="#2ea3ef", labelanchor="n")
    right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    content.grid_columnconfigure(0, weight=1, uniform="group1")
    content.grid_columnconfigure(1, weight=1, uniform="group1")
    content.grid_rowconfigure(0, weight=1)

def showImage(frame, img_size):
    global img_label, left_frame

    img = cv2.resize(frame, (img_size, img_size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(img)
    if (img_label == None):
        img_label = tk.Label(left_frame, image=img, bg="#202d42")
        img_label.image = img
        img_label.pack(padx=20)
    else:
        img_label.configure(image=img)
        img_label.image = img

def getNewSlide(control):
    global img_list, current_slide

    if(len(img_list) > 1):
        if(control == "prev"):
            current_slide = (current_slide-1) % len(img_list)
        else:
            current_slide = (current_slide+1) % len(img_list)

        img_size = left_frame.winfo_height() - 200
        showImage(img_list[current_slide], img_size)

        slide_caption.configure(text = "Image {} of {}".format(current_slide+1, len(img_list)))

def selectMultiImage(opt_menu, menu_var):
    global img_list, current_slide, slide_caption, slide_control_panel

    filetype = [("images", "*.jpg *.jpeg *.png")]
    path_list = filedialog.askopenfilenames(title="Choose atleast 5 images", filetypes=filetype)

    if(len(path_list) < 5):
        messagebox.showerror("Error", "Choose atleast 5 images.")
    else:
        img_list = []
        current_slide = -1

        if (slide_control_panel != None):
            slide_control_panel.destroy()

        for path in path_list:
            img_list.append(cv2.imread(path))

        menu_var.set("")
        opt_menu['menu'].delete(0, 'end')

        for i in range(len(img_list)):
            ch = "Image " + str(i+1)
            opt_menu['menu'].add_command(label=ch, command= tk._setit(menu_var, ch))
            menu_var.set("Image 1")

        img_size =  left_frame.winfo_height() - 200
        current_slide += 1
        showImage(img_list[current_slide], img_size)

        slide_control_panel = tk.Frame(left_frame, bg="#202d42", pady=20)
        slide_control_panel.pack()

        back_img = tk.PhotoImage(file="previous.png")
        next_img = tk.PhotoImage(file="next.png")

        prev_slide = tk.Button(slide_control_panel, image=back_img, bg="#202d42", bd=0, highlightthickness=0,
                            activebackground="#202d42", command=lambda : getNewSlide("prev"))
        prev_slide.image = back_img
        prev_slide.grid(row=0, column=0, padx=60)

        slide_caption = tk.Label(slide_control_panel, text="Image 1 of {}".format(len(img_list)), fg="#ff9800",
                              bg="#202d42", font="Arial 15 bold")
        slide_caption.grid(row=0, column=1)

        next_slide = tk.Button(slide_control_panel, image=next_img, bg="#202d42", bd=0, highlightthickness=0,
                            activebackground="#202d42", command=lambda : getNewSlide("next"))
        next_slide.image = next_img
        next_slide.grid(row=0, column=2, padx=60)


def register(entries, required, menu_var):
    global img_list

    if(len(img_list) == 0):
        messagebox.showerror("Error", "Select Images first.")
        return

    entry_data = {}
    for i, entry in enumerate(entries):
        val = entry[1].get()

        if (len(val) == 0 and required[i] == 1):
            messagebox.showerror("Field Error", "Required field missing :\n\n%s" % (entry[0]))
            return
        else:
            entry_data[entry[0]] = val.lower()

    path = os.path.join('face_samples', "temp_missing_person")
    if not os.path.isdir(path):
        os.mkdir(path)

    no_face = []
    for i, img in enumerate(img_list):
        # Storing Images in directory
        id = registerMissingPerson(img, path, i + 1)
        if(id != None):
            no_face.append(id)

    if(len(no_face) > 0):
        no_face_st = ""
        for i in no_face:
            no_face_st += "Image " + str(i) + ", "
        messagebox.showerror("Registration Error", "Registration failed!\n\nFollowing images do not contain"
                        " a face or the face is too small:\n\n%s"%(no_face_st))
        shutil.rmtree(path, ignore_errors=True)
    else:
        insertData(entry_data)
        rowId=1
        if(rowId >= 0):
            messagebox.showinfo("Success", "Missing Person Registered Successfully.")
            shutil.move(path, os.path.join('face_samples', entry_data["Name"]))

            profile_img_num = int(menu_var.get().split(' ')[1]) - 1
            if not os.path.isdir("profile_pics"):
                os.mkdir("profile_pics")
            cv2.imwrite("profile_pics/missing_person %d.png"%rowId, img_list[profile_img_num])

            goBack()
        else:
            shutil.rmtree(path, ignore_errors=True)
            messagebox.showerror("Database Error", "Some error occured while storing data.")

def on_configure(event, canvas, win):
    canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.itemconfig(win, width=event.width)

# Register
def getPage1():
    global active_page, left_frame, right_frame, heading, img_label
    active_page = 1
    img_label = None
    opt_menu = None
    menu_var = tk.StringVar(root)
    pages[1].lift()

    basicPageSetup(1)
    heading.configure(text="Register Missing Person", bg="#ADD8E6", fg='#055099')
    right_frame.configure(text="Enter Details", fg="#055099", bg="#ADD8E6")

    btn_grid = tk.Frame(left_frame, bg="#ADD8E6")
    btn_grid.pack()

    tk.Button(btn_grid, text="Select Images", command=lambda: selectMultiImage(opt_menu, menu_var), font="Arial 15 bold", bg="#055099",
           fg="white", pady=10, bd=0, highlightthickness=0, activebackground="#ADD8E6",
           activeforeground="white").grid(row=0, column=0, padx=25, pady=25)

    canvas = tk.Canvas(right_frame, bg="#202d42", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand="true", padx=30)
    scrollbar = tk.Scrollbar(right_frame, command=canvas.yview, width=20, troughcolor="#ADD8E6", bd=0,
                          activebackground="#ADD8E6", bg="#055099", relief="raised")
    scrollbar.pack(side="left", fill="y")

    scroll_frame = tk.Frame(canvas, bg="#ADD8E6", pady=20)
    scroll_win = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda event, canvas=canvas, win=scroll_win: on_configure(event, canvas, win))

    input_fields = ("Name", "Contact Number", "Gender", "DOB (YYYY-MM-DD)", "Address", "Email", "Profile Picture")
    ip_len = len(input_fields)
    required = [1, 1, 1, 1, 1, 1]

    entries = []
    for i, field in enumerate(input_fields):
        row = tk.Frame(scroll_frame, bg="#ADD8E6")
        row.pack(side="top", fill="x", pady=15)

        label = tk.Text(row, width=20, height=1, bg="#ADD8E6", fg="#055099", font="Arial 13", highlightthickness=0, bd=0)
        label.insert("insert", field)
        label.pack(side="left")

        label.configure(state="disabled")

        if(i != ip_len-1):
            ent = tk.Entry(row, font="Arial 13", selectbackground="#90ceff")
            ent.pack(side="right", expand="true", fill="x", padx=10)
            entries.append((field, ent))
        else:
            menu_var.set("Image 1")
            choices = ["Image 1"]
            opt_menu = tk.OptionMenu(row, menu_var, *choices)
            opt_menu.pack(side="right", fill="x", expand="true", padx=10)
            opt_menu.configure(font="Arial 13", bg="white", fg="black", bd=0, highlightthickness=0)
            menu = opt_menu.nametowidget(opt_menu.menuname)
            menu.configure(font="Arial 13", bg="white", activebackground="#055099", bd=0)

    tk.Button(scroll_frame, text="Register", command=lambda: register(entries, required, menu_var), font="Arial 15 bold",
           bg="#055099", fg="white", pady=10, padx=30, bd=0, highlightthickness=0, activebackground="#ADD8E6",
           activeforeground="white").pack(pady=25)

def showMissingPersonProfile(name):
    top = tk.Toplevel(bg="#055099")
    top.title("Missing Person Profile")
    top.geometry("1500x900+%d+%d"%(root.winfo_x()+10, root.winfo_y()+10))

    tk.Label(top, text="Missing Person Profile", fg="white", bg="#055099", font="Arial 20 bold", pady=10).pack()

    content = tk.Frame(top, bg="#055099", pady=20)
    content.pack(expand="true", fill="both")
    content.grid_columnconfigure(0, weight=3, uniform="group1")
    content.grid_columnconfigure(1, weight=5, uniform="group1")
    content.grid_rowconfigure(0, weight=1)

    (id, missing_person_data) = retrieveData(name)

    path = os.path.join("profile_pics", "missing_person %d.png"%id)
    profile_img = cv2.imread(path)

    profile_img = cv2.resize(profile_img, (500, 500))
    img = cv2.cvtColor(profile_img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(img)
    img_label = tk.Label(content, image=img, bg="#055099")
    img_label.image = img
    img_label.grid(row=0, column=0)

    info_frame = tk.Frame(content, bg="#055099")
    info_frame.grid(row=0, column=1, sticky='w')

    for i, item in enumerate(missing_person_data.items()):
        tk.Label(info_frame, text=item[0], pady=15, fg="#ADD8E6", font="Arial 15 bold", bg="#055099").grid(row=i, column=0, sticky='w')
        tk.Label(info_frame, text=":", fg="#ADD8E6", padx=50, font="Arial 15 bold", bg="#055099").grid(row=i, column=1)
        val = "---" if (item[1]=="") else item[1]
        tk.Label(info_frame, text=val, fg="white", font="Arial 15", bg="#055099").grid(row=i, column=2, sticky='w')

    address_label = tk.Text(info_frame, width=20, height=1, bg="#ADD8E6", fg="#055099", font="Arial 13", highlightthickness=0, bd=0)
    address_label.grid(row=6, column=1)
    address_label.insert("insert", 'Address Found At')

    address_label.configure(state="disabled")

    address_ent = tk.Entry(info_frame, font="Arial 13", selectbackground="#90ceff")
    address_ent.grid(row=6, column=2)

    contact_label = tk.Text(info_frame, width=20, height=1, bg="#ADD8E6", fg="#055099", font="Arial 13", highlightthickness=0, bd=0)
    contact_label.grid(row=7, column=1)
    contact_label.insert("insert", 'Contact Number')

    contact_label.configure(state="disabled")

    contact_ent = tk.Entry(info_frame, font="Arial 13", selectbackground="#90ceff")
    contact_ent.grid(row=7, column=2)

    print(missing_person_data)

    tk.Button(info_frame, text="Send Mail", 
            command=lambda: send_found_mail(missing_person_data['Name'], missing_person_data['Email'], address_ent.get(), contact_ent.get()), 
            font="Arial 15 bold", bg="#ADD8E6", fg="#055099", pady=10, padx=30, bd=0, highlightthickness=0, 
            activebackground="#ADD8E6", activeforeground="white").grid(row=8, column=1)

def startRecognition():
    global img_read, img_label

    if(img_label == None):
        messagebox.showerror("Error", "No image selected. ")
        return

    missing_person_found_labels = []
    for wid in right_frame.winfo_children():
        wid.destroy()

    frame = cv2.flip(img_read, 1, 0)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    face_coords = detect_faces(gray_frame)

    if (len(face_coords) == 0):
        messagebox.showerror("Error", "Image doesn't contain any face or face is too small.")
    else:
        (model, names) = train_model()
        print('Training Successful. Detecting Faces')
        (frame, recognized) = recognize_face(model, frame, gray_frame, face_coords, names)

        img_size = left_frame.winfo_height() - 40
        frame = cv2.flip(frame, 1, 0)
        showImage(frame, img_size)

        if (len(recognized) == 0):
            messagebox.showerror("Error", "No missing person recognized.")
            return

        for i, missing_person in enumerate(recognized):
            missing_person_found_labels.append(tk.Label(right_frame, text=missing_person[0], bg="#055099", fg='white',
                                            font="Arial 15 bold", pady=20))
            missing_person_found_labels[i].pack(fill="x", padx=20, pady=10)
            missing_person_found_labels[i].bind("<Button-1>", lambda e, name=missing_person[0]:showMissingPersonProfile(name))

def selectImage():
    global left_frame, img_label, img_read
    for wid in right_frame.winfo_children():
        wid.destroy()

    filetype = [("images", "*.jpg *.jpeg *.png")]
    path = filedialog.askopenfilename(title="Choose a image", filetypes=filetype)

    if(len(path) > 0):
        img_read = cv2.imread(path)

        img_size =  left_frame.winfo_height() - 40
        showImage(img_read, img_size)

# Upload Missing Image
def getPage2():
    global active_page, left_frame, right_frame, img_label, heading
    img_label = None
    active_page = 2
    pages[2].lift()

    basicPageSetup(2)
    heading.configure(text="Detect Missing Person", fg="#055099")
    right_frame.configure(text="Detected Missing People", fg="#055099")

    btn_grid = tk.Frame(left_frame, bg="#ADD8E6")
    btn_grid.pack()

    tk.Button(btn_grid, text="Select Image", command=selectImage, font="Arial 15 bold", padx=20, bg="#055099",
            fg="white", pady=10, bd=0, highlightthickness=0, activebackground="#ADD8E6",
            activeforeground="white").grid(row=0, column=0, padx=25, pady=25)
    tk.Button(btn_grid, text="Recognize", command=startRecognition, font="Arial 15 bold", padx=20, bg="#055099",
           fg="white", pady=10, bd=0, highlightthickness=0, activebackground="#ADD8E6",
           activeforeground="white").grid(row=0, column=1, padx=25, pady=25)

def videoLoop(path,model, names):
    p=path
    q=ntpath.basename(p)
    filenam, file_extension = os.path.splitext(q)
    global thread_event, left_frame, webcam, img_label
    start=time.time()
    webcam = cv2.VideoCapture(1)
    old_recognized = []
    missing_person_found_labels = []
    times = []
    img_label = None
    field=['S.No.', 'Name', 'Time']
    g=filenam+'.csv'
    filename = g
    num=0
    print(filename)
    try:
        with open(filename, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(field)   
            while not thread_event.is_set():
                    while (True):
                        (return_val, frame) = webcam.read()
                        print(frame)
                        if (return_val == True):
                            break

                    frame = cv2.flip(frame, 1, 0)
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    face_coords = detect_faces(gray_frame)
                    (frame, recognized) = recognize_face(model, frame, gray_frame, face_coords, names)

                    recog_names = [item[0] for item in recognized]
                    if(recog_names != old_recognized):
                        for wid in right_frame.winfo_children():
                            wid.destroy()
                        del(missing_person_found_labels[:])

                        for i, missing_person in enumerate(recognized):
                            num+=1
                            x=time.time()-start
                            missing_person_found_labels.append(tk.Label(right_frame, text=missing_person[0], bg="#055099", fg='white',
                                                            font="Arial 15 bold", pady=20))
                            missing_person_found_labels[i].pack(fill="x", padx=20, pady=10)
                            missing_person_found_labels[i].bind("<Button-1>", lambda e, name=missing_person[0]: showMissingPersonProfile(name))
                            y=missing_person[0]
                            print(x,y)
                            arr = [num,y,x]
                            csvwriter.writerow(arr)  
                            
                        old_recognized = recog_names

                    img_size = min(left_frame.winfo_width(), left_frame.winfo_height()) - 20

                    showImage(frame, img_size)

    except RuntimeError:
        print("[INFO]Caught Runtime Error")
    except tk.TclError:
        print("[INFO]Caught Tcl Error")

# CCTV surveillance
def getPage4(path='./Missing'):
    p=path
    global active_page, video_loop, left_frame, right_frame, thread_event, heading
    active_page = 4
    pages[4].lift()

    basicPageSetup(4)
    heading.configure(text="Video Surveillance", fg='#055099')
    right_frame.configure(text="Detected Missing People", fg='#055099')
    left_frame.configure(pady=40)

    btn_grid = tk.Frame(right_frame, bg="#ADD8E6")
    btn_grid.pack()

    (model, names) = train_model()
    print('Training Successful. Detecting Faces')

    thread_event = threading.Event()
    thread = threading.Thread(target=videoLoop, args=(p,model, names))
    thread.start()

def getPage3():
    global active_page, video_loop, left_frame, right_frame, thread_event, heading
    active_page = 3
    pages[3].lift()

    basicPageSetup(3)
    heading.configure(text="Video Surveillance")

    btn_grid = tk.Frame(left_frame,bg="#ADD8E6")
    btn_grid.pack()

    tk.Button(btn_grid, text="Select Video", command=selectvideo, font="Arial 15 bold", padx=20, bg="#055099",
                fg="white", pady=10, bd=0, highlightthickness=0, activebackground="#ADD8E6",
                activeforeground="white").grid(row=0, column=0, padx=25, pady=25)

def selectvideo():
    global left_frame, img_label, img_read
    for wid in right_frame.winfo_children():
        wid.destroy()

    filetype = [("video", "*.mp4 *.mkv")]
    path = filedialog.askopenfilename(title="Choose a video", filetypes=filetype)
    p=''
    p=path
    
    if(len(path) > 0):
        getPage4(p)

# Home
tk.Label(pages[0], text="Missing Person Identification System", fg="#055099", bg="#ADD8E6",
      font="Arial 25 bold", pady=30).pack()

logo = tk.PhotoImage(file = r".\img\logo2.png")
tk.Label(pages[0], image=logo, bg="#ADD8E6").pack(side='right')

btn_frame = tk.Frame(pages[0], bg="#ADD8E6", pady=30)
btn_frame.pack()

tk.Button(btn_frame, text="Add Missing Person Details", command=getPage1)
tk.Button(btn_frame, text="Image Surveillance", command=getPage2)
tk.Button(btn_frame, text="Video Surveillance", command=getPage4)

for btn in btn_frame.winfo_children():
    btn.configure(font="Arial 20", width=27, bg="#055099", fg="white",
        pady=15, bd=0, highlightthickness=0, activebackground="#00003F", activeforeground="white")
    btn.pack(pady=30)

pages[0].lift()
root.mainloop()