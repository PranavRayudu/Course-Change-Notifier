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

    const [paused, pause] = useState(false)
    const [range, useRange] = useState(true)

    return <Card bordered={false}>
        <Space direction={"vertical"} style={{width: "100%"}}>

            <div className={AppStyles.heading}>
                <Space direction={"vertical"} style={{width: "100%"}}>
                    <h3>Global Monitor Settings</h3>

                    {/*<Divider orientation={"left"} plain>Global Controls</Divider>*/}
                    <Control label={"Pause"} control={<Switch onChange={pause}/>}/>

                    <Control label={"Refresh Period"} control={
                        <span><InputNumber min={1} defaultValue={5} disabled={paused}/> seconds</span>
                    }/>

                    <Divider orientation={"left"} plain>Time Range</Divider>
                    <Control label={"Use Shutoff"} control={<Switch onChange={useRange} disabled={paused}/>}/>
                    <Control label={"Time Range"} control={<RangePicker disabled={paused || !range}/>}/>
                </Space>
            </div>
        </Space>
    </Card>;
}

export default Settings;


