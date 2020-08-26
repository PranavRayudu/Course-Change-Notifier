import React, {useEffect, useState} from 'react';
import {Redirect, Switch, Route, Link, useLocation} from "react-router-dom";
import {Layout, Menu} from "antd";
import {SettingOutlined} from '@ant-design/icons';
import Courses from "./components/Courses";
import Settings from "./components/Settings";
import UserLogin from "./components/UserLogin";
import NotFound from "./components/NotFound";
import BrowserLogin from "./components/BrowserLogin";

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
    const [logged, setLogged] = useState(false)
    const [redirPath, setRedir] = useState(null)

    useEffect(() => {
        fetch(`/api/v1/login_status`, {
            method: 'GET',
        }).then(res => res.json()).then(data => {
            if (data.user) {
                setLogged(true)
                if (path === '/login')
                    setRedir('/')
            } else {
                setLogged(false)
                setRedir('/login')
            }
        }).catch((err) => {
            setLogged(false)
            setRedir('/login')
        })
    }, [path])

    return (
        <Layout className={AppStyles.layout}>
            {redirPath && <Redirect to={redirPath}/>}
            <Header className={AppStyles.titleBar}>
                <h3 className={AppStyles.title}>UT Course Monitor Dashboard</h3>
            </Header>

            {logged &&
            <Menu selectedKeys={path_key[path]} mode={"horizontal"} className={AppStyles.menu}>
                <Menu.Item key={"courses"}><Link to={"/"}>Courses</Link></Menu.Item>
                <Menu.Item key={"settings"}><Link to={"/settings"}><SettingOutlined/>Settings</Link></Menu.Item>
            </Menu>}

            <Content className={AppStyles.container}>
                {logged && <BrowserLogin/>}
                <Switch>
                    {logged && <Route path={"/"} component={Courses} exact/>}
                    {logged && <Route path={"/settings"} component={Settings}/>}
                    {!logged && <Route path={"/login"} component={UserLogin}/>}
                    {logged && <Route component={NotFound}/>}
                </Switch>
            </Content>

            <Footer className={AppStyles.responsiveSm}>
                UT Course Monitor by <a href={"https://pranavrayudu.netlify.app"}>Pranav Rayudu</a>
            </Footer>
        </Layout>
    );
}

export default App;
