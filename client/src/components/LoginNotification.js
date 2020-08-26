import React, {useEffect, useState} from 'react';
import {message, Modal} from "antd";

function LoginNotification() {

    const [failed, setFailed] = useState(false)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        setLoading(true)
        fetch(`/api/v1/logged_in`, {
            method: 'GET',
        }).then(res => res.json()).then(data => {
            setFailed(!data.status)
        }).catch((err) => {
            setFailed(true)
        }).finally(() => setLoading(false))
    }, [])

    const sendLogin = () => {
        setLoading(true)
        fetch(`/api/v1/logged_in`, {
            method: 'POST',
        }).then(res => res.json()).then(data => {
            if (data.status) message.success('login successful')
            else message.error('unsuccessful login')
            setFailed(!data.status)
        }).catch((err) => {
            message.error('unsuccessful login')
        }).finally(() => setLoading(false))
    }

    return <Modal
        title="Not logged into UT systems"
        okText="Attempt login"
        onOk={sendLogin}
        cancelButtonProps={{style: {display: "None"}}}
        visible={failed}
        closable={false}
        confirmLoading={loading}>
        You need to log into UT to continue checking for courses. Press OK to attempt login (must accept push
        notification on DUO)
    </Modal>
}

export default LoginNotification;


