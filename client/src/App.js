import React, {useEffect, useState} from 'react';
import {Redirect, Switch, Route, Link, useLocation} from "react-router-dom";
import {Layout, Menu, message} from "antd";
import {SettingOutlined} from '@ant-design/icons';
import Courses from "./routes/Courses";
import Settings from "./routes/Settings";
import UserLogin from "./routes/UserLogin";
import NotFound from "./routes/NotFound";
import BrowserLogin from "./components/BrowserLogin";

import '../node_modules/antd/dist/antd.css';
import '../node_modules/antd/dist/antd.dark.css';

import AppStyles from './app.module.scss';
import {connect} from "react-redux";
import {fetchLoginData} from "./store/actions";

const {Header, Footer, Content} = Layout;

const path_key = {
    "/": "courses",
    "/settings": "settings"
}

function App({dispatch, logged, loading}) {

    const path = useLocation().pathname

    useEffect(() => {
        dispatch(fetchLoginData(
            null,
            () => message.error('unable to contact server')
        ))
    }, [dispatch, path])

    const renderRedirect = () => {
        if (!loading && !logged && path !== '/login')
            return <Redirect to={'/login'}/>
        if (!loading && logged && path === '/login')
            return <Redirect to={'/'}/>
        return null
    }

    return (
        <Layout className={AppStyles.layout}>
            {renderRedirect()}
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

// export default App;
const mapStateToProps = state => {
    return {
        logged: state.userLogin,
        loading: state.userLoading,
    }
}

export default connect(mapStateToProps)(App);
