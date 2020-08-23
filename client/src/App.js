import React from 'react';
import {useLocation} from "react-router";
import {Switch, Route, Link,} from "react-router-dom";
import {Layout, Menu} from "antd";
import {SettingOutlined} from '@ant-design/icons';
import Courses from "./components/Courses";
import Settings from "./components/Settings";

import '../node_modules/antd/dist/antd.css';
// import '../node_modules/antd/dist/antd.dark.css';

import AppStyles from './app.module.scss';

const {Header, Footer, Content} = Layout;

const path_key = {
    "/": "courses",
    "/settings": "settings"
}

function App() {

    const path = useLocation().pathname
    return (
        <Layout className={AppStyles.layout}>
            <Header className={AppStyles.titleBar}>
                <h3 className={AppStyles.title}>UT Course Monitor Dashboard</h3>
            </Header>

            <Menu selectedKeys={path_key[path]} mode={"horizontal"} className={AppStyles.menu}>
                <Menu.Item key={"courses"}><Link to={"/"}>Courses</Link></Menu.Item>
                <Menu.Item key={"settings"}><Link to={"/settings"}><SettingOutlined />Settings</Link></Menu.Item>
            </Menu>

            <Content className={AppStyles.container}>
                <div className={AppStyles.content}>
                    <Switch>
                        <Route path={"/"} component={Courses} exact/>
                        <Route path={"/settings"} component={Settings}/>
                    </Switch>
                </div>
            </Content>

            <Footer className={AppStyles.responsiveSm}>
                UT Course Monitor by <a href={"https://pranavrayudu.netlify.app"}>Pranav Rayudu</a>
            </Footer>
        </Layout>
    );
}

export default App;
