import time
import schedule
from course_scraper import scrape_urls
from storage import Storage
from notifier import send_telegram_message


urls = [
    "https://www.udemy.com/courses/it-and-software/it-certification/?closed_captions=en&closed_captions=en_cc&instructional_level=beginner&instructional_level=all&instructional_level=intermediate&instructional_level=expert&lang=en&price=price-free&ratings=4.0&sort=most-reviewed",
    "https://www.udemy.com/courses/it-and-software/other-it-and-software/?closed_captions=en&closed_captions=en_cc&lang=en&price=price-free&ratings=4.0&sort=most-reviewed",
    "https://www.coursera.org/search?language=Arabic&language=English&productTypeDescription=Professional%20Certificates&subtitleLanguage=English&subtitleLanguage=Arabic&topic=Computer%20Science&topic=Information%20Technology&sortBy=BEST_MATCH",
]


storage = Storage("sent_courses.json")


def format_message(course):
    msg = (
        "🔥 New Free Course Found!\n\n"
        f"Platform: {course.get('platform')}\n"
        f"Title: {course.get('title')}\n\n"
        "Enroll Now:\n"
        f"{course.get('link')}"
    )
    return msg


def check_and_notify():
    print("Checking for new courses...")
    try:
        scraped = scrape_urls(urls)
    except Exception as e:
        print("Error during scraping:", e)
        scraped = []

    new_courses = []
    links_to_add = []

    for c in scraped:
        link = c.get("link")
        if not link:
            continue
        if not storage.has(link):
            new_courses.append(c)
            links_to_add.append(link)

    if new_courses:
        for course in new_courses:
            print("New course found!")
            msg = format_message(course)
            try:
                send_telegram_message(msg)
            except Exception as e:
                print("Failed to send message:", e)

        # record them to avoid duplicates in the future
        storage.add_many(links_to_add)
    else:
        print("No new courses.")
        try:
            send_telegram_message("No new courses found.")
        except Exception as e:
            print("Failed to send 'no new courses' message:", e)


def main():
    # run once on start
    check_and_notify()

    # schedule every 2 hours
    schedule.every(2).hours.do(check_and_notify)

    print("Scheduler started. Running every 2 hours.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down.")
            break


if __name__ == "__main__":
    main()
