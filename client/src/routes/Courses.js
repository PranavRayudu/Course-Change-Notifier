import React from 'react';
import {message, Card, Tag, Button, Form, Input, Space, Table} from "antd";
import {PlusOutlined, DeleteOutlined, ReloadOutlined, PauseOutlined, CaretRightOutlined} from '@ant-design/icons';
import {red, yellow, green, grey} from '@ant-design/colors';
import Pluralize from "../components/Pluralize";
import AppStyles from "../app.module.scss";
import {connect} from "react-redux";


const tagColors = {
    'open': green.primary,
    'open; reserved': green.primary,
    'reserved': yellow.primary,
    'waitlisted': yellow.primary,
    'waitlisted; reserved': yellow.primary,
    'closed': red.primary,
    'cancelled': grey.primary,
    'invalid': grey.primary,
}


class Courses extends React.Component {

    columns = [
        {
            title: 'ID',
            dataIndex: 'uid',
            render: (text, row) =>
                row.status === 'invalid' ? text :
                    <a href={`https://utdirect.utexas.edu/apps/registrar/course_schedule/${this.state.sid}/${text}/`}>{text}</a>,
            sorter: (a, b) => a.uid.localeCompare(b.uid),
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Abbr.',
            dataIndex: 'abbr',
            render: text => text ? text : '...',
        },
        {
            title: 'Title',
            dataIndex: 'title',
            render: text => text ? text : '...',
        },
        {
            title: 'Professor',
            dataIndex: 'prof',
            render: text => text ? text : '...',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            render: text => <Tag color={tagColors[text]}>{text}</Tag>,
        },
        {
            // title: 'Control',
            dataIndex: 'paused',
            render: (text, row) => text ?
                <Button type={"dashed"} icon={<CaretRightOutlined/>}
                        disabled={row.status === 'invalid'}
                        onClick={() => this.resumeCourse(row.uid)}/> :
                <Button type={"dashed"} icon={<PauseOutlined/>}
                        disabled={row.status === 'invalid'}
                        onClick={() => this.pauseCourse(row.uid)}/>,
        },
        {
            // title: 'Action',
            dataIndex: 'uid',
            render: (text, row) => row.status !== 'invalid' && <a
                href={`https://utdirect.utexas.edu/registration/registration.WBX?s_ccyys=${this.state.sid}&s_af_unique=${text}`}
                target="_blank" rel="noopener noreferrer">Register</a>,
        },
    ];

    constructor(props) {
        super(props);

        this.state = {refreshing: false, uid: '', sid: '', data: [], selected: []}
        this.refreshData = this.refreshData.bind(this)
        this.handleSubmit = this.handleSubmit.bind(this)
    }

    componentDidMount() {
        this.getSid()
        this.refreshData()
        setInterval(this.refreshData, 1000 * 60 * 5) // every 5 min
    }

    handleSubmit(e) {
        // event.preventDefault()
        this.addCourse(this.state.uid)
        this.setState({uid: ''})
    }

    startLoading() {
        this.setState({loading: true})
    }

    endLoading() {
        this.setState({loading: false})
    }

    getSid() {
        fetch(`/api/v1/config`, {
            method: 'GET',
        }).then(res => res.json()).then(data => {
            this.setState({sid: data.sid})
        }).catch((err) => {
            message.error('Unable to get semester info')
        })
    }

    refreshData() {
        this.startLoading()

        fetch(`/api/v1/courses`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
        }).then(res => res.json()).then(data => {
            data.forEach(course => {
                course.key = course.uid
            })
            this.setState({data: data})
        }).catch((err) => {
            message.error('Unable to refresh courses')
        })
            .finally(() => this.endLoading())
    }

    addCourse(uid) {
        this.startLoading()
        fetch(`/api/v1/courses/${uid}`, {
            method: 'POST',
            headers: {
                'Accept': 'text/plain',
                'Content-Type': 'application/json',
            },
        }).then(() => this.refreshData())
            .catch((err) => {
                message.error('Unable to add course')
            })
            .finally(() => this.endLoading())
    }

    deleteCourses(courses) {
        this.startLoading()
        let fetches = []
        courses.forEach(course => {
            fetches.push(fetch(`/api/v1/courses/${course.uid}`, {
                method: 'DELETE',
                headers: {
                    'Accept': 'text/plain',
                    'Content-Type': 'application/json',
                },
            }))
        })

        Promise.all(fetches)
            .then(() => this.refreshData())
            .catch((err) => {
                message.error('Unable to delete courses')
            })
            .finally(() => this.endLoading())
    }


    pauseCourse(uid) {
        this.startLoading()
        fetch(`/api/v1/courses/${uid}/pause?status=true`, {
            method: 'POST',
        }).then(() => this.refreshData())
            .catch((err) => {
                message.error('Unable to pause course')
            })
            .finally(() => this.endLoading())
    }

    resumeCourse(uid) {
        this.startLoading()
        fetch(`/api/v1/courses/${uid}/pause?status=false`, {
            method: 'POST',
        }).then(() => this.refreshData())
            .catch((err) => {
                message.error('Unable to pause course')
            })
            .finally(() => this.endLoading())
    }

    render() {

        // rowSelection object indicates the need for row selection
        const rowSelection = {
            onChange: (selectedRowKeys, selectedRows) => {
                console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows);
                // setSelected(selectedRows)
                this.setState({selected: selectedRows})
            },

            // getCheckboxProps: record => ({
            //     disabled: record.name === 'Disabled User', // Column configuration not to be checked
            //     name: record.name,
            // }),
        };

        let tableHeader = <div className={AppStyles.heading}>
            <h3>Tracking {this.state.data.length}&nbsp;
                <Pluralize count={this.state.data.length}
                           word={"Course"}/></h3>

            <Space>
                <Form onFinish={this.handleSubmit} layout={"inline"}>
                    <Input.Group compact>
                        {/*<Form.Item name={"uid"} rules={[{required: true}]} style={{width: "50%"}}>*/}
                        <Input required
                               placeholder={"Course ID"}
                               pattern={"[0-9]{5}"}
                               value={this.state.uid}
                               onChange={e => this.setState({uid: e.target.value})}
                               style={{maxWidth: "100px"}}
                        />
                        {/*</Form.Item>*/}
                        {/*<Form.Item style={{width: "50%"}}>*/}
                        <Button type={"primary"}
                                htmlType={'submit'}>
                            <span className={AppStyles.hideSm}>Add</span>
                            <PlusOutlined/>
                        </Button>
                        {/*</Form.Item>*/}
                    </Input.Group>
                </Form>

                <Button type={"secondary"}
                        onClick={this.refreshData}>
                    <span className={AppStyles.hideSm}>Refresh</span><ReloadOutlined/>
                </Button>
                <Button type={"danger"}
                        onClick={() => this.deleteCourses(this.state.selected)}
                        disabled={this.state.selected.length === 0}>
                    <span className={AppStyles.hideSm}>Delete</span><DeleteOutlined/>
                </Button>
            </Space>
        </div>

        return <Card bordered={false}>
            <Space direction={"vertical"} style={{width: "100%"}}>
                {tableHeader}
                <Table
                    rowSelection={{
                        type: "checkbox",
                        ...rowSelection
                    }}
                    columns={this.columns}
                    dataSource={this.state.data}
                    loading={this.state.loading}
                    pagination={false}
                    scroll={{x: 700}}
                    // bordered
                    // title={() => tableHeader}
                />
            </Space>
        </Card>;
    }
}

// export default Courses

const mapStateToProps = state => {
    return {
        sid: state.sid,
        data: state.courses,
        refreshing: state.coursesLoading,
    }
}

// function mapDispatchToProps(dispatch)

export default connect(mapStateToProps)(Courses);


