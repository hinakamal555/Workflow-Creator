import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import re
import utils
import plotly.express as px

# Fetch workflows
workflows = utils.get_all_workflows()

# Initialize session state for input fields if not already done
if "name" not in st.session_state:
    st.session_state.name = ""
if "type" not in st.session_state:
    st.session_state.type = ""
if "delay_in" not in st.session_state:
    st.session_state.delay_in = ""
if "dnis" not in st.session_state:
    st.session_state.dnis = ""
if "tradb_tag_id" not in st.session_state:
    st.session_state.tradb_tag_id = ""
if "template_id" not in st.session_state:
    st.session_state.template_id = ""
if "template" not in st.session_state:
    st.session_state.template = ""
if "variables" not in st.session_state:
    st.session_state.variables = ""
if "badges" not in st.session_state:
    st.session_state.badges = []

def workflow_creator():
    st.markdown("### Create Campaign")
    with st.form(key='campaign_form'):
        campaign_name = st.text_input(label='Enter campaign name')
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        list_id = utils.create_list(campaign_name)
        if not list_id:
            st.error("Campaign Name Already Exists")
        else:
            st.write("Campaign Created Successfully")
    st.divider()

    st.markdown("### Create Action")
    if len(workflows) > 0:
        workflow_name = st.selectbox(label='Select Campaign', options=[i['name'] for i in workflows])
        selected_workflow = next((i for i in workflows if i['name'] == workflow_name), None)
        st.session_state.badges = []
        if selected_workflow is not None:
            with st.container(border=True):
                name = st.text_input(label='*Enter action name', key="name")
                action_type = st.selectbox(label='Select action type', options=['Email', 'SMS'])
                delay = st.number_input(label='Enter delay', step=1, value=0, key="delay")
                delay_in = st.selectbox(label='Select delay in', options=['Minutes', 'Hours', 'Days'])
                dnis = st.text_input(label='Enter dnis', placeholder='xxx-xxx-xxxx', max_chars=12, key="dnis")
                tradb_tag_id = st.text_input(label='Enter tradb tag id', key="tradb_tag_id")
                if action_type == 'Email':
                    template_id = st.text_input(label='Enter template id', key="template_id")
                else:
                    template_id = st.empty()

                if action_type == 'SMS':
                    st.caption("**Use {d{variable}} to add dynamic values")
                    st.caption("**Example: {d{first_name}}")
                    st.caption("**The DNIS should be inserted into the template using curly braces, like so: {}")
                    template = st.text_area(label='*Enter template', key="template")

                    st.session_state.badges = re.findall(r'd\[(.*?)\]', template)

                    if template and len(st.session_state.badges) == 0:
                        st.caption("**No dynamic variables in the template")
                    else:
                        st.caption("**Dynamic Variables in the template")

                if action_type == 'Email':
                    st.caption("**Add dynamic variables separated by comma")
                    st.caption("**Example: first_name, last_name")
                    variables = st.text_input(label='*Enter dynamic templates', key="variables")
                    if variables:
                        st.session_state.badges = [variable.strip() for variable in variables.split(',')]
                        print(st.session_state.badges)
                workflow = selected_workflow['_id']
                if len(st.session_state.badges) > 0:
                    badge_list = [(badge, 'default') for badge in st.session_state.badges]
                    ui.badges(badge_list=badge_list, class_name="flex gap-2", key="badges1")
                submit_button = st.button(label='Submit')
                if submit_button:
                    if action_type == 'SMS' and template == '':
                        st.error("Template is required")
                    if name == '' or action_type == '' or delay == '' or delay_in == '':
                        st.error("Name, Type, Delay and Delay In are required")
                    else:

                        if action_type == 'Email':
                            action_type = 'send_email'
                        else:
                            action_type = 'sendsms'

                        if delay_in == 'Minutes':
                            delay_in = 'minute'
                        elif delay_in == 'Hours':
                            delay_in = 'hours'
                        else:
                            delay_in = 'days'

                        action = {
                            "name": name,
                            "type": action_type,
                            "delay": delay,
                            "delay_in": delay_in,
                            "active": True,
                            "tradb_tag_id": tradb_tag_id,
                            "dnis": dnis,
                            "workflow": workflow,
                            "dynamic_variables": st.session_state.badges,
                            "event_date": "dateCreated",
                        }

                        if action_type == 'sendsms':
                            action['10_dlc'] = True
                            action['ignoreCompliance'] = True
                            action['template'] = template
                            action['template_id'] = ""
                        else:
                            action['template_id'] = template_id
                        print(action)
                        res = utils.add_action(action)
                        if res:
                            st.write("Action Created Successfully")
                        else:
                            st.error("Error Creating Action")
                        
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])

    if uploaded_file is not None:
        print(uploaded_file.name)
        print(utils.get_file_extension(uploaded_file.name))
        dataframe = pd.read_csv(uploaded_file)
        st.write("File Uploaded Successfully")
        st.write("File Extension:", utils.get_file_extension(uploaded_file.name))
        st.write("File Name:", uploaded_file.name)
        st.markdown("## Data")
        st.markdown("## Data Analysis")
        st.write("Number of Rows:", dataframe.shape[0])
        st.write("Number of Columns:", dataframe.shape[1])
        st.write("Columns:", dataframe.columns)
        st.write(dataframe.head(5))

        dataframe.loc[:12000, 'line_type'] = 'landline'  # Corrected line
        state_counts = dataframe['State'].value_counts()

        fig = px.bar(state_counts, x=state_counts.index, y=state_counts.values, labels={'x':'State', 'y':'Count'})
        st.plotly_chart(fig)

        phone_types = dataframe['line_type'].value_counts()

        fig = px.pie(phone_types, values=phone_types.values, names=phone_types.index, title='Phone Types', labels={'names':'Phone Type'})
        st.plotly_chart(fig)

        # Fetch workflows
workflows = utils.get_all_workflows()

# Sidebar navigation
st.sidebar.title("Navigation")
options = st.sidebar.radio("Go to", ["Workflow Creator", "Contact Suppression"])

# Page display
if options == "Workflow Creator":
    workflow_creator()
elif options == "Contact Suppression":
    utils.contact_suppression()