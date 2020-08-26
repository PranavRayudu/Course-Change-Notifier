import React, {useState} from 'react';
import {Row, Col, InputNumber, TimePicker, Space, Switch, Divider, Card} from "antd";
import AppStyles from "../app.module.scss";

const {RangePicker} = TimePicker

function Control({label, control}) {

    return <Row>
        <Col span={8}>{label}</Col>
        <Col span={16}>{control}</Col>
    </Row>
}

function Settings() {

    const [range, useRange] = useState(true)

    return <Card bordered={false}>
        <Space direction={"vertical"} style={{width: "100%"}}>
            <div className={AppStyles.heading}>
                <Space direction={"vertical"} style={{width: "100%"}}>
                    <h3>Global Monitor Settings</h3>

                    <Control label={"Refresh Period"} control={
                        <span><InputNumber min={1} defaultValue={180}/>&nbsp;seconds</span>
                    }/>

                    <Divider orientation={"left"} plain>Time Range</Divider>
                    <Control label={"Use time range"} control={<Switch onChange={useRange}/>}/>
                    <Control label={"Range"} control={<RangePicker format={"HH:mm"} disabled={!range}/>}/>
                </Space>
            </div>
        </Space>
    </Card>;
}

export default Settings;


