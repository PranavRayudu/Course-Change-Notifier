import React, {useEffect, useState} from 'react';
import {message, Modal} from "antd";
import {connect} from "react-redux";
import {postBrowserLogin} from "../store/actions";

function BrowserLogin({dispatch, success, loading}) {
    const sendLogin = () => {
        dispatch(postBrowserLogin(
            () => message.success('login successful'),
            () => message.error('unsuccessful login')
        ))
    }

    return <Modal
        title="Not logged into UT systems"
        okText="Attempt login"
        onOk={sendLogin}
        cancelButtonProps={{style: {display: "None"}}}
        visible={!success}
        closable={false}
        confirmLoading={loading}>
        You need to log into UT to continue checking for courses. Press OK to attempt login (must accept push
        notification on DUO)
    </Modal>
}

const mapStateToProps = state => {
    return {
        success: state.browserLogin,
        loading: state.browserLoading,
    }
}

export default connect(mapStateToProps)(BrowserLogin);

