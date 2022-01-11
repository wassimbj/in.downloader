from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from time import time
import os
from pathlib import Path


def cleanFileName(name):
    return str(name).replace(":", "-").replace("?", "")


def pathToDownlods():
    return str(Path.home() / "Downloads")


base_url = "https://www.linkedin.com"

options = webdriver.ChromeOptions()
# change this one according to where you have the binary
options.binary_location = "D:\workspace\chrome.sync\Chrome-bin\chrome.exe"
options.headless = True
prefs = {"profile.default_content_settings.popups": 0,
         # IMPORTANT - ENDING SLASH V IMPORTANT
         "download.default_directory": pathToDownlods(),
         "directory_upgrade": True}
options.add_experimental_option("prefs", prefs)

options.add_argument("--log-level=3")
s = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)
# driver.maximize_window()
# driver.set_window_size(1700, 1700)  # you can change this based on your PC


def login(email, password):
    """
    opens the login modal, enter the login details and submit the form
    @returns true for success and Excpetion otherwise
    """
    try:
        driver.get(base_url+"/uas/login")
        sleep(3)
        # enter email and password
        driver.execute_script(
            'document.querySelector("form #username").value = "'+email+'"')
        driver.execute_script(
            'document.querySelector("form #password").value = "'+password+'"')
        # submit the form
        driver.execute_script('document.querySelector("form button").click()')
        return True
    except Exception as e:
        print("Login Error: ")
        print(e)
        return e


def getCourseContentsLinks():
    """
    loop throught the course contents, get the categories and the lessons for each category
    @returns: a dict
    """

    menu = driver.execute_script("""
      // category and links indexes will be the same here
        let data = {
            totalLessons: 0,
            categories: [],
            links: []
        }
        let categories = document.querySelectorAll(".classroom-toc-section")
        for(let i = 0; i < categories.length; i++){
            let category = String(categories[i].querySelector(".classroom-toc-section__toggle-title").textContent).trim()
            let menuLinks = categories[i].querySelectorAll(".classroom-toc-section__items a")
            let menu = []
            for(let j = 0; j < menuLinks.length; j++){
                menu.push({
                    url: menuLinks[j].getAttribute("href")
                })
                data.totalLessons += 1
            }
            data.categories.push(category)
            data.links.push(menu)
        }
      return data
   """)
    # return the data object
    return dict(menu)


def downloadCourse(url):
    # ? please remove any "/" at the end of the URL
    # url example: https://www.linkedin.com/learning/learn-apache-kafka-for-beginners
    """
    navigate to the lesson link, take a screenshot and convert it to pdf

    @params: <url> = course url, example is above
    @returns: a stats dict which has the total lessons and the successfully downloaded files.
    """
    try:
        driver.get(url)
        sleep(2)
        # courseName = driver.execute_script("return document.title")
        splitUrl = url.split("/")
        courseName = splitUrl[splitUrl.index(
            "learning")+1].replace("-", " ").title()
        print("\n ########## {} ######### \n".format(courseName))
        if (courseName == ""):
            print("EMPTY COURSE NAME !!")
            return
        pathToSaveEverything = os.path.join(pathToDownlods(), courseName)
        Path(pathToSaveEverything).mkdir(parents=True, exist_ok=True)
        downloadedFiles = 0
        content = getCourseContentsLinks()
        # print(content)
        stats = {
            "totalLessons": content.get("totalLessons"),
            "totalDownloaded": 0
        }

        for i, categoryName in enumerate(content.get("categories")):
            print("\n")
            print(categoryName)
            print("-------------------------------------")
            courseCategoryDir = os.path.join(
                pathToSaveEverything, cleanFileName(categoryName))

            Path(courseCategoryDir).mkdir(parents=True, exist_ok=True)

            for j, course in enumerate(content.get("links")[i]):
                urlToCouse = str(base_url) + str(course.get("url")).replace(
                    "autoplay=true", "autoplay=false")

                videoFileName = downloadVideo(urlToCouse)
                print("DOWNLOADING...")
                # wait until we download the video or timeout
                end_time = time() + (10 * 60)
                while not os.path.exists(os.path.join(pathToDownlods(), videoFileName)):
                    sleep(1)
                    if time() > end_time:
                        print("TIMED_OUT !!!")
                        return False
                sleep(1)

                print("MOVING...")
                os.rename(os.path.join(pathToDownlods(), videoFileName),
                          os.path.join(courseCategoryDir, f"{j}_{videoFileName}"))
                print("Downloaded ["+videoFileName+"]")
                downloadedFiles += 1

        stats["totalDownloaded"] = downloadedFiles
        return stats
    except Exception as e:
        print("downloadCourse ERROR: " + e)
        return e


"""
! How to download it
    1- append a link element on the body
        document.createElement("a")
        <a href="/images/myw3schoolsimage.jpg" download="w3logo">
    2- click it to download the video
    3- move the downloaded file from the /Downloads folder to the right one
        os.rename(src, dst)
"""


def downloadVideo(url):
    driver.get(url)
    sleep(2)
    # get video src, append an a tag, click it to download the video
    videoSrc = driver.execute_script(
        "return document.querySelector('video').getAttribute('src')")
    videoTitle = driver.execute_script("return document.title")
    videoFileName = f"{cleanFileName(videoTitle)}.mp4"

    driver.get(videoSrc)
    sleep(2)
    driver.execute_script(f"""
            let downloadLink = document.createElement('a')
            downloadLink.text = 'Download Video'
            downloadLink.setAttribute('href', '{videoSrc}') // video src
            downloadLink.setAttribute(
                'download', '{videoFileName}') // videoFileName

            document.body.append(downloadLink)
            downloadLink.click()
        """)

    return videoFileName


if __name__ == "__main__":
    try:

        # getting the data
        print("\n\n ------------------------------------------------------- \n")
        email = input("Your email: ")
        password = input("your password: ")
        print("\n")
        courseUrl = input("Course url: ")
        print("\n ------------------------------------------------------- \n")

        # the real stuff
        result = login(email, password)
        if result != True:
            print("LOGIN ERROR")
            raise Exception(result)

        print("\n LOGGING IN... \n")
        sleep(3)  # wait until we login
        print("\n DOWNLOADING... \n")
        downloadStats = downloadCourse(courseUrl)

        print(f"""
            \n FINISHED. \n
            Total lessons: {downloadStats.get("totalLessons")}
            \n
            Total downloaded: {downloadStats.get("totalDownloaded")}
        """)

    except Exception as e:
        print("\n FAILED !!")
        print(e)
    finally:
        driver.quit()
