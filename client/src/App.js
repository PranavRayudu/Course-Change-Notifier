import React, {useEffect} from 'react';
import {Link, Redirect, Route, Switch, useLocation} from "react-router-dom";
import {connect} from "react-redux";
import {Layout, Menu, message} from "antd";
import {SettingOutlined} from '@ant-design/icons';

import {fetchConfigData, fetchLoginData} from "./store/actions";

import '../node_modules/antd/dist/antd.css';
// import '../node_modules/antd/dist/antd.dark.css';

import AppStyles from './app.module.scss';
import BrowserLogin from "./components/BrowserLogin";
import Courses from "./routes/Courses";
import NotFound from "./routes/NotFound";
import Settings from "./routes/Settings";
import UserLogin from "./routes/UserLogin";


const {Header, Footer, Content} = Layout;

const path_key = {
    "/": "courses",
    "/settings": "settings"
}

function sid_to_text(sid) {
    let year = parseInt(sid.substring(0, 4))
    let sem = parseInt(sid.substring(4))

    const sem_to_season = {
        2: 'Spring',
        6: 'Summer',
        9: 'Fall'
    }

    return [sem_to_season[sem], year].join(' ')
}

function App({dispatch, logged, loading, sid}) {

    const path = useLocation().pathname

    useEffect(() => {
        if (!logged) dispatch(fetchLoginData(
            null,
            () => message.error('unable to contact server')
        ))
        if (logged) dispatch(fetchConfigData(
            null,
            () => message.error('unable to contact server')
        ))
    }, [dispatch, logged, path])

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
                <h3 className={AppStyles.title}>UT Course Monitor Dashboard {sid && ('for ' + sid_to_text(sid))}</h3>
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

const mapStateToProps = state => {
    return {
        logged: state.userLogin,
        loading: state.userLoading,
        sid: state.sid,
    }
}

export default connect(mapStateToProps)(App);
