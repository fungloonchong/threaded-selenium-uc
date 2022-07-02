from concurrent import futures
from multiprocessing import Semaphore

from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

import undetected_chromedriver as uc

"""
Handles the task queue

A function can be allocated to the task queue to be executed by n number of webdrivers.
The function scheduled for the task queue should only contain 1 argument (tuple) whereby the the first item is the driver object, arg[1:] can be programmed as required.
"""
class QueueHandler:
    def __init__(self, max_worker: int = 0):
        # if max_worker is not defined, get the optimal number by func
        if max_worker > 0:
            self.__max_worker = max_worker
        else:
            self.__max_worker = self.get_optimal_worker_count()
        
        # initialize the driverhandler, executors and semaphores
        self.__drivers = DriverHandler(self.__max_worker)
        self.__executor = futures.ThreadPoolExecutor(max_workers=self.__max_worker)
        self.__mutex = Semaphore(self.__max_worker)

        self.__results = []
        self.__results_mutex = Semaphore(1)

        self.__futures = []
    
    """
    Assign a new task to execute func
    """
    def new_task(self, func, args):
        self.__mutex.acquire()

        new_args = (self.__drivers.acquire_driver(), args)
        
        future = self.__executor.submit(func, new_args)
        future.add_done_callback(self.task_done)

        self.__futures.append(future)

    """
    Callback when the task has been completed
    """
    def task_done(self, future):
        self.__mutex.release()

        driver, retval = future.result()

        # write back results
        self.__results_mutex.acquire()
        self.__results.append(retval)
        self.__results_mutex.release()

        self.__drivers.release_driver(driver)

        return retval

    """
    Compute the optimal number of worker

    TODO: actually compute that.
    """
    def get_optimal_worker_count(self):
        return 5 # hard coded for now

    """
    Get the first result that is available
    """
    def get_results(self):
        self.__results_mutex.acquire()

        while not self.__results:
            pass

        retval = self.__results.pop(0)
        self.__results_mutex.release()

        return retval

    """
    Get all the results that is available
    """
    def get_all_results(self):
        self.__results_mutex.acquire()

        while not self.__results:
            pass

        retval = self.__results

        self.__results = []
        self.__results_mutex.release()

        return retval

    """
    Get all the results when all the futures has been completed
    """
    def all_task_completed(self):
        return futures.wait(self.__futures)

"""
Handles the webdrivers
"""
class DriverHandler:
    def __init__(self, 
        driver_count,
        executable_path=ChromeDriverManager().install()
    ):
        self.__drivers = []
        self.__free_drivers = []
        self.__mutex = Semaphore(1)

        print(f"Drivers requested: {driver_count}")

        if driver_count > 0:
            for i in range(driver_count):
                print(f"Spawning driver {i}")
                service = Service(executable_path=executable_path)

                options = uc.ChromeOptions()
                driver = uc.Chrome(service=service, options=options)

                self.__drivers.append(driver)
                self.__free_drivers.append(driver)

    """
    Gets a driver
    """
    def acquire_driver(self):
        self.__mutex.acquire()

        while len(self.__free_drivers) == 0:
            pass

        retval = self.__free_drivers.pop(0)

        self.__mutex.release()

        return retval

    """
    Release a driver
    """
    def release_driver(self, driver):
        self.__mutex.acquire()

        if driver in self.__drivers and driver not in self.__free_drivers:
            self.__free_drivers.append(driver)
            self.__mutex.release()
        else:
            return False

        return True

"""
Sample function: Wait for YT's query where the results are ready. Print out the title of the document
"""
def get_title(args):
    driver, url = args

    print(f"Running get_title on driver with url {url}")

    driver.get(url)
    WebDriverWait(driver, timeout=10).until(expected_conditions.visibility_of_element_located((By.XPATH, '//*[@id="video-title"]/yt-formatted-string')))

    return driver, driver.title  

if __name__ == "__main__":

    # creates the queue
    t = QueueHandler()

    # first list of urls
    test = ["https://youtube.com/results?search_query=tonight+show", "https://youtube.com/results?search_query=hello+world"]

    # assigning the tasks to the queue
    for i in test:
        t.new_task(get_title, (i))

    # assigning the tasks to the queue
    futures_results_done, futures_results_not_done = t.all_task_completed()

    print("Results of completed futures (blocking until all futures are completed):")
    for i in futures_results_done:
        print(i.result()[1])

    # second list of urls
    test2 = []

    # crafting fake requests
    test2_base_url = "https://youtube.com/results?search_query=rwby+episode+"
    for i in range(23):
        test2.append(f"{test2_base_url}{i}")

    # assigning the tasks to the queue
    for i in test2:
        t.new_task(get_title, (i))

    # block till all futures are completed
    futures_results_done, futures_results_not_done = t.all_task_completed()

    print()
    print("Results of completed futures (blocking until all futures are completed):")
    for i in futures_results_done:
        print(i.result()[1])    

    print()
    print("Results of all completed futures (non-blocking. Returns any completed futures):")
    print(t.get_all_results())
