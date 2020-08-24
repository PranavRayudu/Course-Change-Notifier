import React, {useState} from 'react';
import {Input, Space, Card, Form, Button, message} from "antd";
import AppStyles from "../app.module.scss";
import {Redirect} from "react-router-dom";

const layout = {
    labelCol: {span: 8},
    wrapperCol: {span: 16},
}

const tailLayout = {
    wrapperCol: {offset: 8, span: 16},
}

function Login() {

    const [redirect, setRedirect] = useState(null)

    const onFinish = values => {
        let formData = new FormData()
        formData.append('id', values.id)
        formData.append('password', values.password)

        fetch(`/login`, {
            method: 'POST',
            body: formData,
        }).then(res => {
            if (res.status !== 200)
                throw new Error('login failed')
            setRedirect('/')
        }).catch((err) => {
            message.error('Login attempt failed')
        })
    }

    return <Card bordered={false} style={{width: '340px', margin: 'auto'}}>
        {redirect && <Redirect to={redirect}/>}
        <Space direction={"vertical"} style={{width: "100%"}}>
            <div className={AppStyles.heading}>
                <Space direction={"vertical"}>
                    <h3>Login using your UT Credentials</h3>
                    <Form {...layout} onFinish={onFinish} name={"login form"}>
                        <Form.Item label={'UT EID'} name={'id'}
                                   rules={[{required: true, message: 'enter your UT EID'}]}>
                            <Input/>
                        </Form.Item>
                        <Form.Item label={'password'} name={'password'}
                                   rules={[{required: true, message: 'enter your UT password'}]}>
                            <Input.Password/>
                        </Form.Item>
                        <Form.Item {...tailLayout}>
                            <Button type={"primary"} htmlType={"submit"}>Submit</Button>
                        </Form.Item>
                    </Form>
                </Space>
            </div>
        </Space>
    </Card>;
}

export default Login;


