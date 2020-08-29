import React from 'react';
import {connect} from "react-redux";
import {Input, Space, Card, Form, Button, message} from "antd";
import {postUserLogin} from "../store/actions";
import AppStyles from "../app.module.scss";

const layout = {
    labelCol: {span: 8},
    wrapperCol: {span: 16},
}

const tailLayout = {
    wrapperCol: {offset: 8, span: 16},
}

function UserLogin({dispatch, loading}) {

    const onFinish = values => {
        let formData = new FormData()
        formData.append('id', values.id)
        formData.append('password', values.password)
        dispatch(postUserLogin(formData,
            () => message.success('Successfully logged in'),
            () => message.error('Unable to login in')))
    }

    return <Card bordered={false} style={{width: '340px', margin: 'auto'}}>
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
                            <Button type={"primary"} loading={loading} htmlType={"submit"}>Submit</Button>
                        </Form.Item>
                    </Form>
                </Space>
            </div>
        </Space>
    </Card>;
}


const mapStateToProps = state => {
    return {
        loading: state.browserLoading,
        // success: state.userLogin,
    }
}

export default connect(mapStateToProps)(UserLogin);

