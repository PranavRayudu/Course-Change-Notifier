import React, {useEffect, useState} from 'react';
import {Alert} from "antd";

function LoginNotification() {

    const [failed, setFailed] = useState(false)

    useEffect(() => {
        fetch(`/api/v1/logged_in`, {
            method: 'GET',
        }).then(res => res.json()).then(data => {
            setFailed(!data.status)
        }).catch((err) => {
            setFailed(true)
        })
    })

    const sendLogin = () => {
        fetch(`/api/v1/logged_in`, {
            method: 'POST',
        }).then(res => res.text()).then(data => {
            console.log(data)
        }).catch((err) => {

        })
    }

    if (!failed) return null;
    return <Alert
        message="Login to UT failed"
        closeText={'Try Again'}
        onClose={sendLogin}
        type="error"
        showIcon
        closable

        style={{marginBottom: 24}}
    />
}

export default LoginNotification;


