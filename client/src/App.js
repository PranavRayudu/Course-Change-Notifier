import React, {useState} from 'react';
import {Layout, Menu} from "antd";
import Courses from "./components/Courses";
import Settings from "./components/Settings";

import '../node_modules/antd/dist/antd.css';
// import '../node_modules/antd/dist/antd.dark.css';

import AppStyles from './app.module.scss';

const {Header, Footer, Content} = Layout;


function App() {

    const [nav, setNav] = useState('courses');

    let handleClick = e => {
        setNav(e.key);
    };

    let routes = {
        'courses': <Courses/>,
        'settings': <Settings/>
    }

    return (
        <Layout className={AppStyles.layout}>
            <Header>
                <h3 className={AppStyles.title}>UT Course Monitor Dashboard</h3>
            </Header>

            <Menu onClick={handleClick} selectedKeys={[nav]} mode={"horizontal"} className={AppStyles.menu}>
                <Menu.Item key={"courses"}>Courses</Menu.Item>
                <Menu.Item key={"settings"}>Settings</Menu.Item>
            </Menu>

            <Content className={AppStyles.container}>
                <div className={AppStyles.content}>
                    {routes[nav]}
                </div>
            </Content>

            <Footer>
                UT Course Monitor by <a href={"https://pranavrayudu.netlify.app"}>Pranav Rayudu</a>
            </Footer>
        </Layout>
    );
}

export default App;
