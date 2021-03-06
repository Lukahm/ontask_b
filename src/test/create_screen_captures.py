# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import StringIO
import os

from PIL import Image
from django.conf import settings
from django.shortcuts import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

import test
from dataops import pandas_db


class element_has_full_opacity(object):
    """
    Detect when an element has opacity equal to 1

    locator - used to find the element
    returns the WebElement once opacity is equal to 1
    """

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        if element.value_of_css_property('opacity') == '1':
            return element
        else:
            return False


class ScreenTests(test.OntaskLiveTestCase):
    weight = 1024
    height = 1800
    prefix = ''
    workflow_name = 'BIOL1011'
    description = 'Course on Cell Biology'
    modal_xpath = "//div[@id='modal-item']/div[@class='modal-dialog']/div[" \
                  "@class='modal-content']"

    @staticmethod
    def img_path(f):
        return os.path.join(
            settings.BASE_DIR(),
            'test',
            'images',
            f)

    def wait_for_page(self, title=None, element_id=None):
        if title:
            WebDriverWait(self.selenium, 10).until(
                EC.title_is(title)
            )

        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'div-spinner'))
        )
        WebDriverWait(self.selenium, 10).until(
            EC.invisibility_of_element_located((By.ID, 'img-spinner'))
        )

        if element_id:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, element_id))
            )

    def element_ss(self, xpath, fname):
        """
        Take the snapshot of the element given by xpath and stores it in the
        file with name fname
        :param xpath: Xpath to access one element of the html page
        :param fname: file to store the result
        :return: Nothing
        """
        Image.open(StringIO.StringIO(
            self.selenium.find_element_by_xpath(xpath).screenshot_as_png)
        ).save(self.img_path(self.prefix + fname))

    @classmethod
    def setUpClass(cls):
        super(ScreenTests, cls).setUpClass()
        cls.selenium.set_window_size(cls.weight, cls.height)


class ScreenTutorialTest(ScreenTests):

    def setUp(self):
        super(ScreenTutorialTest, self).setUp()
        test.create_users()

    def test_ss_00(self):
        """
        Create a workflow, upload data and merge
        :return:
        """

        # Login
        self.login('instructor1@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        #
        # Empty list of workflows
        #
        self.element_ss("//body", 'workflow_index_empty.png')

        #
        # Create new workflow
        #
        self.selenium.find_element_by_class_name(
            'js-create-workflow').click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )
        self.selenium.find_element_by_id('id_name').send_keys(
            self.workflow_name
        )
        self.selenium.find_element_by_id(
            'id_description_text'
        ).send_keys(self.description)

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_create.png')

        # click in the OK button to return
        self.selenium.find_element_by_xpath(
            "//button[@type='submit']"
        ).click()
        # Wait for the next page to load
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'workflow-area')
            )
        )

        # Take a picture of the empty details
        self.element_ss("//body", 'workflow_details_empty.png')

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)


class ScreenImportTest(ScreenTests):

    def setUp(self):
        super(ScreenImportTest, self).setUp()
        test.create_users()

    def test_ss_01(self):
        """
        Create a workflow, upload data and merge
        :return:
        """

        # Login
        self.login('instructor1@bogus.com')

        # Open Import page
        self.open(reverse('workflow:import'))
        self.wait_for_page('OnTask :: Import workflows')

        #
        # Import workflow
        #
        self.selenium.find_element_by_id('id_name').send_keys(
            self.workflow_name
        )
        self.selenium.find_element_by_id('id_file').send_keys(
            os.path.join(settings.BASE_DIR(),
                         '..',
                         'initial_workflow.gz')
        )

        # Picture of the body
        self.element_ss("//body", 'workflow_import.png')

        # Click the import button
        self.selenium.find_element_by_xpath(
            "//form/div/button[@type='Submit']"
        ).click()
        self.wait_for_page(title='OnTask :: Workflows')

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)


class ScreenTestFixture(ScreenTests):
    fixtures = ['../initial_workflow/initial_workflow.json']
    filename = os.path.join(
        settings.BASE_DIR(),
        '..',
        'initial_workflow',
        'initial_workflow.sql'
    )

    wflow_name = 'combine columns'

    def setUp(self):
        super(ScreenTestFixture, self).setUp()
        pandas_db.pg_restore_table(self.filename)

        # Insert a SQL Connection
        # sqlc = SQLConnection(
        #     name='remote server',
        #     description_txt='Server with student records',
        #     conn_type='mysql',
        #     conn_driver='',
        #     db_user='remote_db_user',
        #     db_password=True,
        #     db_host='dbserver.bogus.com',
        #     db_port=None,
        #     db_name='demographics',
        #     db_table='s_records'
        # )
        # sqlc.save()

    def tearDown(self):
        pandas_db.delete_all_tables()
        super(ScreenTestFixture, self).tearDown()

    def test_sql_admin(self):
        # Login
        self.login('superuser@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        #
        # List of workflows, navigation
        #
        self.element_ss("//body", 'workflow_superuser_index.png')

        #
        # Ops/Edit column
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='sqlconn-table']/tbody/tr[1]/td[11]/div/button[1]"
        ).click()
        self.selenium.find_element_by_class_name(
            'js-sqlconn-edit'
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_superuser_sql_edit.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_workflow(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        #
        # List of workflows, navigation
        #
        self.element_ss("//body", 'workflow_index.png')

        #
        # Navigation bar, details
        #
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        # Take picture of the navigation bar
        self.element_ss("//body/div[3]", 'navigation_bar.png')

        # Take picture of the body
        self.element_ss("//body", 'workflow_details.png')

        #
        # New column modal
        #
        self.selenium.find_element_by_class_name(
            'js-workflow-column-add'
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )
        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_add_column.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        #
        # Attributes
        #
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-area']/div/button[3]"
        ).click()
        self.selenium.find_element_by_link_text('Attributes').click()
        self.wait_for_page(title='OnTask :: Attributes')

        # Take picture of the attribute page.
        self.element_ss("//body", 'workflow_attributes.png')

        # Click back to the details page
        self.selenium.find_element_by_link_text('Back').click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # Share
        #
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-area']/div/button[3]"
        ).click()
        self.selenium.find_element_by_link_text('Share').click()
        self.wait_for_page(title='OnTask :: Share')

        # Take picture of the attribute page.
        self.element_ss("//body", 'workflow_share.png')

        # Click back to the details page
        self.selenium.find_element_by_link_text('Back').click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # EXPORT
        #
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-area']/div/button[3]"
        ).click()
        self.selenium.find_element_by_link_text('Export').click()
        self.wait_for_page(title='OnTask :: Export Workflow')

        # Take picture of the export page.
        self.element_ss("//body", 'workflow_export.png')

        # Click back to the details page
        self.selenium.find_element_by_xpath(
            "//div[@class='modal-footer']/button[@type='button']"
        ).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # RENAME
        #
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-area']/div/button[3]"
        ).click()
        self.selenium.find_element_by_xpath(
            "//button[contains(@class, 'js-workflow-update')]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_rename.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        #
        # FLUSH DATA
        #
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-area']/div/button[3]"
        ).click()
        self.selenium.find_element_by_xpath(
            "//button[contains(@class, 'js-workflow-flush')]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_flush.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        #
        # DELETE
        #
        self.selenium.find_element_by_xpath(
            "//div[@id='workflow-area']/div/button[3]"
        ).click()
        self.selenium.find_element_by_xpath(
            "//button[contains(@class, 'js-workflow-delete')]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_delete.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_details(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        # Open workflow
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        # Table of columns (separated)
        self.element_ss("//div[@id='column-table_wrapper']",
                        'wokflow_columns.png')

        #
        # Ops/Edit Column
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='column-table']/tbody/tr[1]/td[5]/div/button[1]"
        ).click()
        self.selenium.find_element_by_class_name(
            'js-workflow-column-edit'
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'workflow_column_edit.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_dataops(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        # Open workflow
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # Dataops/Merge CSV Merge Step 1
        #
        self.selenium.find_element_by_link_text("Dataops").click()
        self.selenium.find_element_by_link_text("Data Upload/Merge").click()

        # Picture of the body
        self.element_ss("//body", 'dataops_datauploadmerge.png')

        self.selenium.find_element_by_link_text("CSV Upload/Merge").click()
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('OnTask :: Upload/Merge CSV')
        )
        self.selenium.find_element_by_id('id_file').send_keys(
            os.path.join(settings.BASE_DIR(),
                         '..',
                         'initial_workflow',
                         'initial_workflow.csv')
        )

        # Picture of the body
        self.element_ss("//body", 'dataops_csvupload.png')

        #
        # Dataops/Merge CSV Merge Step 2
        #
        # Click the NEXT button
        self.selenium.find_element_by_xpath(
            "//button[@type='Submit']"
        ).click()
        self.wait_for_page()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@id='id_make_key_2']")
            )
        )
        # Unckeck the columns that won't be keys
        for k_num in [2, 3, 40, 45, 46, 47, 49, 50, 51, 59, 61, 64]:
            self.selenium.find_element_by_id(
                'id_make_key_{0}'.format(k_num)
            ).click()

        # Picture of the body
        self.element_ss("//body", 'dataops_upload_merge_step2.png')

        #
        # Dataops/Merge CSV Merge Step 3
        #
        # Click the NEXT button
        self.selenium.find_element_by_xpath(
            "//button[@type='Submit']"
        ).click()
        self.wait_for_page()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//select[@id='id_dst_key']")
            )
        )

        #
        # Dataops/Merge CSV Merge Step 4
        #
        # Click the NEXT button
        # Select left merge
        Select(self.selenium.find_element_by_id(
            'id_how_merge'
        )).select_by_value('left')

        # Picture of the body
        self.element_ss("//body", 'dataops_upload_merge_step3.png')

        # Click the NEXT button
        self.selenium.find_element_by_xpath(
            "//button[@type='Submit']"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'page-header'),
                'Step 4: Review and confirm')
        )

        # Picture of the body
        self.element_ss("//body", 'dataops_upload_merge_step4.png')

        #
        # Dataops/Merge Excel Merge
        #
        # Click the NEXT button
        # Go to DataOps/Merge
        self.selenium.find_element_by_link_text("Dataops").click()
        self.selenium.find_element_by_link_text("Data Upload/Merge").click()
        self.selenium.find_element_by_link_text("Excel Upload/Merge").click()
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('OnTask :: Upload/Merge Excel')
        )

        # Picture of the body
        self.element_ss("//body", 'dataops_upload_excel.png')

        #
        # Dataops/Merge SQL Connection
        #
        self.selenium.find_element_by_link_text("Dataops").click()
        self.selenium.find_element_by_link_text("Data Upload/Merge").click()
        self.selenium.find_element_by_link_text("SQL Connections").click()
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('OnTask :: SQL Connections')
        )

        # Picture of the body
        self.element_ss("//body", 'dataops_SQL_available.png')

        # Click on the link RUN
        self.selenium.find_element_by_link_text('Run').click()

        # Picture of the body
        self.element_ss("//body", 'dataops_SQL_run.png')

        #
        # Dataops: Transform
        #
        self.selenium.find_element_by_link_text("Dataops").click()
        self.selenium.find_element_by_link_text("Transform").click()
        WebDriverWait(self.selenium, 10).until(
            EC.title_is('OnTask :: Transform')
        )

        # Picture of the body
        self.element_ss("//body", 'dataops_transform_list.png')

        # Click to run test_plugin_1
        self.selenium.find_element_by_xpath(
            "//table[@id='transform-table']/tbody/tr[4]/td[7]/div/a"
        ).click()

        # Picture of the body
        self.element_ss("//body", 'dataops_transformation_run.png')

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_table(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        # Open workflow
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # Table
        #
        self.selenium.find_element_by_link_text("Table").click()
        self.wait_for_page(element_id='table-data_previous')

        # Picture of the body
        self.element_ss("//body", 'table.png')

        # Picture of the buttons
        self.element_ss("//div[@id='table-content']/div[1]",
                        'table_buttons.png')

        #
        # Table Views
        #
        self.selenium.find_element_by_link_text("Views").click()
        self.wait_for_page(title='OnTask :: Table Views')

        # Picture of the body
        self.element_ss("//body", 'table_views.png')

        #
        # Specific table view
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='view-table']/tbody/tr[2]/td[4]/div/a"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'table-data_previous'))
        )

        # Picture of the body
        self.element_ss("//body", 'table_view_view.png')

        # Click edit view definition
        self.selenium.find_element_by_class_name('js-view-edit').click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )
        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'table_view_edit.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_action(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        # Open workflow
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # Actions
        #
        self.selenium.find_element_by_link_text("Actions").click()
        self.wait_for_page(element_id='action-table_previous')

        # Picture of the body
        self.element_ss("//body", 'actions.png')

        #
        # Edit Action In
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[4]/td[5]/div/a"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'column-selected-table_previous')
            )
        )

        # Picture of the body
        self.element_ss("//body", 'action_edit_action_in.png')

        #
        # Run Action In
        #
        self.selenium.find_element_by_link_text("Actions").click()
        self.wait_for_page(element_id='action-table_previous')
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[4]/td[5]/div/a[2]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'actioninrun-data_previous')
            )
        )

        # Picture of the body
        self.element_ss("//body", 'action_run_action_in.png')

        #
        # Enter data manually
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='actioninrun-data']/tbody/tr[1]/td[1]/a"
        ).click()
        self.wait_for_page(title='OnTask :: Enter Data')

        # Picture of the body
        self.element_ss("//body", 'action_enter_data_action_in.png')

        #
        # Action In URL enable
        #
        self.selenium.find_element_by_link_text("Actions").click()
        self.wait_for_page(element_id='action-table_previous')
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[4]/td[5]/div/button[1]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )
        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'action_action_in_URL.png')

        # click in the OK button to return
        self.selenium.find_element_by_xpath(
            "//button[@type='submit']"
        ).click()
        # MODAL WAITING
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )
        self.wait_for_page(element_id='action-table_previous')

        #
        # Edit Action Out
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[3]/td[5]/div/a"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//h4[@id='filter-set']/div/button")
            )
        )

        # Picture of the body
        self.element_ss("//body", 'action_edit_action_out.png')

        #
        # Edit filter in action out
        #
        self.selenium.find_element_by_class_name('js-filter-edit').click()
        # Wait for the form to modify the filter
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )

        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'action_action_out_edit_filter.png')

        # Click in the cancel button
        self.selenium.find_element_by_xpath(
            "//div[@id='modal-item']//button[@data-dismiss='modal']"
        ).click()
        # Wail until the modal-open element disappears
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )
        WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//h4[@id='filter-set']/div/button")
            )
        )

        #
        # Editor parts of action out
        #
        self.element_ss("//h4[@id='filter-set']",
                        'action_action_out_filterpart.png')

        # Take picture of the condition set
        self.element_ss("//div[@id='condition-set']",
                        'action_action_out_conditionpart.png')

        # Take picture of the html editor
        self.element_ss("//div[@id='html-editor']",
                        'action_action_out_editorpart.png')

        #
        # Action row
        #
        self.selenium.find_element_by_link_text("Actions").click()
        self.wait_for_page(element_id='action-table_previous')

        # Picture of the action row
        self.element_ss(
            "//table[@id='action-table']/tbody/tr[3]",
            'action_action_ops.png'
        )

        #
        # Send emails
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[3]/td[5]/div/a[2]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.ID, 'email-action-request-data')
            )
        )

        # Picture of the body
        self.element_ss("//body", 'action_email_request_data.png')

        #
        # Action URL
        #
        self.selenium.find_element_by_link_text("Actions").click()
        self.wait_for_page(element_id='action-table_previous')
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[3]/td[5]/div/button[1]"
        ).click()
        WebDriverWait(self.selenium, 10).until(
            element_has_full_opacity((By.XPATH, "//div[@id='modal-item']"))
        )
        # Take picture of the modal
        self.element_ss(self.modal_xpath, 'action_URL_on.png')

        # click in the OK button to return
        self.selenium.find_element_by_xpath(
            "//button[@type='submit']"
        ).click()
        # MODAL WAITING
        WebDriverWait(self.selenium, 10).until_not(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'modal-open')
            )
        )
        self.wait_for_page(element_id='action-table_previous')

        # End of session
        self.logout()

        # Close the db_engine
        # pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_scheduler(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        # Open workflow
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # Actions
        #
        self.selenium.find_element_by_link_text("Actions").click()
        self.wait_for_page(element_id='action-table_previous')

        #
        # Schedule email
        #
        self.selenium.find_element_by_xpath(
            "//table[@id='action-table']/tbody/tr[3]/td[5]/div/button[2]"
        ).click()
        self.selenium.find_element_by_link_text('Schedule').click()
        self.wait_for_page(title='OnTask :: Schedule email send')

        self.selenium.find_element_by_id('id_subject').send_keys(
            'Your preparation activities for the week'
        )
        Select(self.selenium.find_element_by_id(
            'id_email_column')
        ).select_by_visible_text('email')
        self.selenium.find_element_by_id('id_track_read').click()
        dt_widget = self.selenium.find_element_by_xpath(
            "//input[@id='id_execute']"
        )
        self.selenium.execute_script(
            "arguments[0].value = '2110-07-05 17:30:51';",
            dt_widget
        )

        # Take picture of the export page.
        self.element_ss("//body", 'schedule_action_email.png')

        # Click the schedule button
        self.selenium.find_element_by_xpath(
            "//button[@type='Submit']"
        ).click()
        self.wait_for_page(title='OnTask :: Email scheduled')

        #
        # Scheduler
        #
        self.selenium.find_element_by_link_text("Scheduler").click()
        self.wait_for_page(element_id='scheduler-table_previous')

        # Take picture of the export page.
        self.element_ss("//body", 'schedule.png')

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)

    def test_ss_logs(self):
        # Login
        self.login('instructor01@bogus.com')

        # Open Workflows page
        self.open(reverse('workflow:index'))
        self.wait_for_page(title='OnTask :: Workflows',
                           element_id='workflow-table_previous')

        # Open workflow
        self.selenium.find_element_by_link_text(self.workflow_name).click()
        self.wait_for_page(title='OnTask :: Details',
                           element_id='column-table_previous')

        #
        # Logs
        #
        self.selenium.find_element_by_link_text("Logs").click()
        self.wait_for_page(element_id='log-table_previous')

        # Take picture of the body
        self.element_ss("//body", 'logs.png')

        # End of session
        self.logout()

        # Close the db_engine
        pandas_db.destroy_db_engine(pandas_db.engine)
